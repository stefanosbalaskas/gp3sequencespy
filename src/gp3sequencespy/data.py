from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np
import pandas as pd
from pandas.api.types import is_bool_dtype, is_numeric_dtype

from ._exceptions import ValidationError
from ._types import PrepareResult, ValidationResult

_AUDIT_COLUMNS = [
    "sequence_id", "row", "column", "issue_code", "severity",
    "value", "message", "action",
]
_DECISION_COLUMNS = ["step", "policy", "affected_rows", "details"]


def _empty_audit() -> pd.DataFrame:
    return pd.DataFrame({
        "sequence_id": pd.Series(dtype="object"),
        "row": pd.Series(dtype="Int64"),
        "column": pd.Series(dtype="object"),
        "issue_code": pd.Series(dtype="object"),
        "severity": pd.Series(dtype="object"),
        "value": pd.Series(dtype="object"),
        "message": pd.Series(dtype="object"),
        "action": pd.Series(dtype="object"),
    })[_AUDIT_COLUMNS]


def _empty_decisions() -> pd.DataFrame:
    return pd.DataFrame({
        "step": pd.Series(dtype="object"),
        "policy": pd.Series(dtype="object"),
        "affected_rows": pd.Series(dtype="int64"),
        "details": pd.Series(dtype="object"),
    })[_DECISION_COLUMNS]


def _assert_column_name(value: str | None, argument: str, *, allow_none: bool = False) -> None:
    if allow_none and value is None:
        return
    if not isinstance(value, str) or value == "":
        raise ValidationError(f"`{argument}` must be a single non-missing column name.")


def _normalize_cols(value: Sequence[str] | None, argument: str) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, Sequence):
        raise ValidationError(f"`{argument}` must contain unique, non-missing character values.")
    out = list(value)
    if any(not isinstance(x, str) or not x for x in out) or len(set(out)) != len(out):
        raise ValidationError(f"`{argument}` must contain unique, non-missing character values.")
    return out


def _is_list_column(series: pd.Series) -> bool:
    return bool(series.map(lambda x: isinstance(x, (list, dict, set, tuple, np.ndarray)) if x is not None else False).any())


def _missing_mask(series: pd.Series) -> pd.Series:
    miss = series.isna().copy()
    if pd.api.types.is_object_dtype(series.dtype) or pd.api.types.is_string_dtype(series.dtype) or isinstance(series.dtype, pd.CategoricalDtype):
        text = series.astype("string")
        miss = miss | text.str.strip().eq("").fillna(False)
    return miss.astype(bool)


def _value_text(values: Any) -> str | None:
    if isinstance(values, pd.Series):
        seq = values.tolist()
    elif isinstance(values, (list, tuple, np.ndarray, pd.Index, pd.api.extensions.ExtensionArray)):
        seq = list(values)
    else:
        seq = [values]
    if not seq:
        return None

    def _format_value(value: Any) -> str:
        if value is None or value is pd.NA:
            return "<NA>"
        try:
            missing = pd.isna(value)
        except (TypeError, ValueError):
            missing = False
        if isinstance(missing, (bool, np.bool_)) and bool(missing):
            return "<NA>"
        return str(value)

    return " | ".join(_format_value(value) for value in seq[:5])


def _issue(
    *,
    issue_code: str,
    severity: str,
    message: str,
    action: str,
    sequence_id: Any = None,
    row: int | None = None,
    column: str | None = None,
    value: Any = None,
) -> dict[str, Any]:
    return {
        "sequence_id": None if sequence_id is None or pd.isna(sequence_id) else str(sequence_id),
        "row": row,
        "column": column,
        "issue_code": issue_code,
        "severity": severity,
        "value": None if value is None else str(value),
        "message": message,
        "action": action,
    }


def _audit_frame(issues: list[dict[str, Any]]) -> pd.DataFrame:
    if not issues:
        return _empty_audit()
    df = pd.DataFrame(issues, columns=_AUDIT_COLUMNS)
    rank = {"error": 0, "review": 1, "info": 2}
    df["__sev"] = df["severity"].map(rank)
    df["__seq"] = df["sequence_id"].fillna(chr(0x10FFFF))
    row_sentinel = np.iinfo(np.int32).max
    df["__row"] = [row_sentinel if pd.isna(value) else int(value) for value in df["row"]]
    df = df.sort_values(["__sev", "__seq", "__row", "issue_code"], kind="stable").drop(columns=["__sev", "__seq", "__row"])
    df = df.reset_index(drop=True)
    df["row"] = pd.array(df["row"], dtype="Int64")
    return df[_AUDIT_COLUMNS]


def _status(audit: pd.DataFrame) -> str:
    if (audit["severity"] == "error").any():
        return "fail"
    if (audit["severity"] == "review").any():
        return "review"
    return "pass"


def _mapping(sequence_id_col: str, order_col: str, state_col: str, duration_col: str | None, metadata_cols: list[str]) -> pd.DataFrame:
    roles = ["sequence_id", "sequence_order", "state"]
    columns = [sequence_id_col, order_col, state_col]
    if duration_col is not None:
        roles.append("duration")
        columns.append(duration_col)
    roles.extend(f"metadata:{x}" for x in metadata_cols)
    columns.extend(metadata_cols)
    return pd.DataFrame({"role": roles, "source_column": columns})


def _format_order_key(value: Any) -> str:
    try:
        return format(float(value), ".17f").rstrip("0").rstrip(".") or "0"
    except Exception:
        return str(value)


def audit_sequence_data(
    data: pd.DataFrame,
    sequence_id_col: str,
    order_col: str,
    state_col: str,
    duration_col: str | None = None,
    metadata_cols: Sequence[str] | None = None,
    expected_states: Sequence[Any] | None = None,
) -> pd.DataFrame:
    """Audit long-format sequence data without modifying it."""
    if not isinstance(data, pd.DataFrame):
        raise ValidationError("`data` must be a data frame.")
    _assert_column_name(sequence_id_col, "sequence_id_col")
    _assert_column_name(order_col, "order_col")
    _assert_column_name(state_col, "state_col")
    _assert_column_name(duration_col, "duration_col", allow_none=True)
    metadata = _normalize_cols(metadata_cols, "metadata_cols")
    if expected_states is not None and isinstance(expected_states, (dict, pd.DataFrame)):
        raise ValidationError("`expected_states` must be an atomic vector or `NULL`.")

    mapped_core = [x for x in [sequence_id_col, order_col, state_col, duration_col] if x is not None]
    if len(set(mapped_core)) != len(mapped_core):
        raise ValidationError("Required column mappings must refer to distinct columns.")
    if any(x in mapped_core for x in metadata):
        raise ValidationError("`metadata_cols` must not repeat required mapped columns.")

    issues: list[dict[str, Any]] = []
    if data.columns.duplicated().any():
        dup = data.columns[data.columns.duplicated()].tolist()
        issues.append(_issue(
            issue_code="duplicate_column_names", severity="error", value=_value_text(dup),
            message="The data frame contains duplicated column names.",
            action="Rename duplicated columns before validation.",
        ))
        return _audit_frame(issues)

    required = {"sequence_id": sequence_id_col, "sequence_order": order_col, "state": state_col}
    if duration_col is not None:
        required["duration"] = duration_col
    for role, col in required.items():
        if col not in data.columns:
            issues.append(_issue(column=col, issue_code="missing_required_column", severity="error", value=col,
                message=f"The mapped {role} column is absent from `data`.", action="Correct the column mapping or add the required column."))
    for col in [x for x in metadata if x not in data.columns]:
        issues.append(_issue(column=col, issue_code="missing_metadata_column", severity="error", value=col,
            message="A requested metadata column is absent from `data`.", action="Correct `metadata_cols` or add the metadata column."))
    if not all(c in data.columns for c in [sequence_id_col, order_col, state_col]):
        return _audit_frame(issues)
    if len(data) == 0:
        issues.append(_issue(issue_code="empty_data", severity="error", message="The input contains no sequence rows.", action="Provide at least one ordered state observation."))
        return _audit_frame(issues)

    seq = data[sequence_id_col]
    order = data[order_col]
    state = data[state_col]
    valid_seq = not _is_list_column(seq)
    valid_state = not _is_list_column(state)
    valid_order = is_numeric_dtype(order.dtype) and not is_bool_dtype(order.dtype)
    if not valid_seq:
        issues.append(_issue(column=sequence_id_col, issue_code="invalid_sequence_id_type", severity="error", message="Sequence identifiers must use an atomic vector.", action="Convert sequence identifiers to character, factor, or numeric."))
    if not valid_state:
        issues.append(_issue(column=state_col, issue_code="invalid_state_type", severity="error", message="States must use an atomic vector.", action="Convert states to character, factor, or numeric."))
    if not valid_order:
        issues.append(_issue(column=order_col, issue_code="invalid_order_type", severity="error", message="Sequence order must be numeric.", action="Convert the order column to finite numeric positions."))
    if not valid_seq or not valid_state:
        return _audit_frame(issues)

    seq_missing = _missing_mask(seq)
    state_missing = _missing_mask(state)
    seq_text = seq.astype("string")
    state_text = state.astype("string")
    for idx in np.flatnonzero(seq_missing.to_numpy()):
        issues.append(_issue(row=idx+1, column=sequence_id_col, issue_code="missing_sequence_id", severity="error", value=_value_text(seq.iloc[idx]), message="The row has no usable sequence identifier.", action="Supply a sequence identifier or remove the row explicitly."))
    for idx in np.flatnonzero(state_missing.to_numpy()):
        sid = None if seq_missing.iloc[idx] else seq_text.iloc[idx]
        issues.append(_issue(sequence_id=sid, row=idx+1, column=state_col, issue_code="missing_state", severity="error", value=_value_text(state.iloc[idx]), message="The row has no usable state value.", action="Supply a state or apply an explicit missing-state policy."))

    order_missing = pd.Series(True, index=data.index)
    order_finite = pd.Series(False, index=data.index)
    if valid_order:
        arr = pd.to_numeric(order, errors="coerce").astype(float)
        order_missing = order.isna()
        order_finite = pd.Series(np.isfinite(arr), index=data.index)
        for idx in np.flatnonzero(order_missing.to_numpy()):
            issues.append(_issue(sequence_id=seq_text.iloc[idx], row=idx+1, column=order_col, issue_code="missing_sequence_order", severity="error", value=_value_text(order.iloc[idx]), message="The row has no sequence-order value.", action="Supply the order explicitly; order is never inferred."))
        for idx in np.flatnonzero((~order_missing & ~order_finite).to_numpy()):
            issues.append(_issue(sequence_id=seq_text.iloc[idx], row=idx+1, column=order_col, issue_code="non_finite_order", severity="error", value=_value_text(order.iloc[idx]), message="The sequence-order value is not finite.", action="Replace infinite or non-finite order values."))

    valid_seq_pos = np.flatnonzero((~seq_missing).to_numpy())
    if valid_order:
        valid_order_pos = np.flatnonzero((~seq_missing & ~order_missing & order_finite).to_numpy())
        if len(valid_order_pos):
            keys = [(str(seq_text.iloc[i]), _format_order_key(order.iloc[i])) for i in valid_order_pos]
            counts: dict[tuple[str, str], int] = {}
            for k in keys: counts[k] = counts.get(k, 0) + 1
            for pos, k in zip(valid_order_pos, keys, strict=True):
                if counts[k] > 1:
                    issues.append(_issue(sequence_id=seq_text.iloc[pos], row=pos+1, column=order_col, issue_code="duplicated_position", severity="error", value=_value_text(order.iloc[pos]), message="The sequence contains a duplicated position.", action="Correct the position or apply an explicit first/last policy."))
            groups: dict[str, list[int]] = {}
            for pos in valid_order_pos:
                groups.setdefault(str(seq_text.iloc[pos]), []).append(int(pos))
            eps = np.sqrt(np.finfo(float).eps)
            for sid, positions in groups.items():
                current = np.asarray([float(order.iloc[i]) for i in positions])
                if np.any(np.diff(current) < 0):
                    issues.append(_issue(sequence_id=sid, row=positions[0]+1, column=order_col, issue_code="unordered_rows", severity="review", value=_value_text(current), message="Rows are not ordered within the sequence.", action="Sort deterministically by sequence and order."))
                unique_order = np.unique(current)
                if len(unique_order)>1 and np.all(np.abs(unique_order-np.round(unique_order)) < eps):
                    gaps=np.flatnonzero(np.diff(unique_order)>1)
                    if len(gaps):
                        gap_text=", ".join(f"{unique_order[g]:g}->{unique_order[g+1]:g}" for g in gaps)
                        issues.append(_issue(sequence_id=sid,row=positions[0]+1,column=order_col,issue_code="missing_positions",severity="review",value=gap_text,message="The sequence has gaps between integer positions.",action="Confirm that omitted positions are intentional."))
                ordered_positions=sorted(positions,key=lambda i:(float(order.iloc[i]),i))
                prev: str | None=None
                prev_missing=True
                for pos in ordered_positions:
                    cur_missing=bool(state_missing.iloc[pos]); cur=str(state_text.iloc[pos])
                    if not cur_missing and not prev_missing and cur==prev:
                        issues.append(_issue(sequence_id=seq_text.iloc[pos],row=pos+1,column=state_col,issue_code="consecutive_repeated_state",severity="review",value=_value_text(state.iloc[pos]),message="The state repeats consecutively within the sequence.",action="Preserve or collapse repeats through an explicit policy."))
                    prev=cur; prev_missing=cur_missing

    if len(valid_seq_pos):
        groups: dict[str,list[int]]={}
        for pos in valid_seq_pos: groups.setdefault(str(seq_text.iloc[pos]),[]).append(int(pos))
        for sid,positions in groups.items():
            usable=[i for i in positions if not state_missing.iloc[i]]
            if len(usable)==1:
                i=usable[0]
                issues.append(_issue(sequence_id=sid,row=i+1,column=state_col,issue_code="single_state_sequence",severity="review",value=_value_text(state.iloc[i]),message="The sequence contains only one usable state row.",action="Confirm that single-state sequences are admissible."))

    if duration_col is not None and duration_col in data.columns:
        dur=data[duration_col]
        valid_duration=is_numeric_dtype(dur.dtype) and not is_bool_dtype(dur.dtype)
        if not valid_duration:
            issues.append(_issue(column=duration_col,issue_code="invalid_duration_type",severity="error",message="Duration must be numeric.",action="Convert duration to a numeric scale."))
        else:
            vals=pd.to_numeric(dur,errors="coerce").astype(float)
            miss=dur.isna(); finite=pd.Series(np.isfinite(vals),index=data.index)
            for idx in np.flatnonzero(miss.to_numpy()):
                issues.append(_issue(sequence_id=seq_text.iloc[idx],row=idx+1,column=duration_col,issue_code="missing_duration",severity="review",value=_value_text(dur.iloc[idx]),message="The row has no duration value.",action="Confirm whether missing duration is admissible."))
            for idx in np.flatnonzero((~miss & ~finite).to_numpy()):
                issues.append(_issue(sequence_id=seq_text.iloc[idx],row=idx+1,column=duration_col,issue_code="non_finite_duration",severity="error",value=_value_text(dur.iloc[idx]),message="The duration value is not finite.",action="Replace infinite or non-finite durations."))
            for idx in np.flatnonzero((~miss & finite & (vals<0)).to_numpy()):
                issues.append(_issue(sequence_id=seq_text.iloc[idx],row=idx+1,column=duration_col,issue_code="negative_duration",severity="error",value=_value_text(dur.iloc[idx]),message="The duration value is negative.",action="Correct or explicitly exclude the row."))
            for idx in np.flatnonzero((~miss & finite & (vals==0)).to_numpy()):
                issues.append(_issue(sequence_id=seq_text.iloc[idx],row=idx+1,column=duration_col,issue_code="zero_duration",severity="review",value="0",message="The duration value is zero.",action="Preserve, drop, or reject zero duration explicitly."))

    for col in [x for x in metadata if x in data.columns]:
        vals=data[col]
        if _is_list_column(vals):
            issues.append(_issue(column=col,issue_code="invalid_metadata_type",severity="error",message="Metadata columns must use atomic vectors.",action="Convert list-columns before sequence preparation.")); continue
        if not len(valid_seq_pos): continue
        groups: dict[str,list[int]]={}
        for pos in valid_seq_pos: groups.setdefault(str(seq_text.iloc[pos]),[]).append(int(pos))
        for sid,positions in groups.items():
            unique=pd.unique(vals.iloc[positions].dropna().astype(str))
            if len(unique)>1:
                issues.append(_issue(sequence_id=sid,row=positions[0]+1,column=col,issue_code="inconsistent_metadata",severity="error",value=_value_text(unique),message=f"Metadata column `{col}` varies within the sequence.",action="Correct the metadata or redefine the sequence identifier."))

    if expected_states is not None:
        expected={str(x) for x in expected_states}
        for idx in np.flatnonzero((~state_missing & ~state_text.isin(expected)).to_numpy()):
            issues.append(_issue(sequence_id=seq_text.iloc[idx],row=idx+1,column=state_col,issue_code="unknown_state",severity="review",value=_value_text(state.iloc[idx]),message="The state is absent from `expected_states`.",action="Preserve, drop, or reject unknown states explicitly."))

    if isinstance(state.dtype,pd.CategoricalDtype):
        observed=set(state.loc[~state_missing].astype(str))
        unused=[str(x) for x in state.cat.categories if str(x) not in observed]
        if unused:
            issues.append(_issue(column=state_col,issue_code="unused_state_levels",severity="info",value=_value_text(unused),message="The factor contains unused state levels.",action="Preserve or drop unused levels explicitly."))
    return _audit_frame(issues)


def validate_sequence_data(
    data: pd.DataFrame,
    sequence_id_col: str,
    order_col: str,
    state_col: str,
    duration_col: str | None = None,
    metadata_cols: Sequence[str] | None = None,
    expected_states: Sequence[Any] | None = None,
) -> ValidationResult:
    metadata=_normalize_cols(metadata_cols,"metadata_cols")
    audit=audit_sequence_data(data,sequence_id_col,order_col,state_col,duration_col,metadata,expected_states)
    counts={s:int((audit["severity"]==s).sum()) for s in ["error","review","info"]}
    nseq=0
    if sequence_id_col in data.columns and not _is_list_column(data[sequence_id_col]):
        series=data[sequence_id_col]; usable=~_missing_mask(series)
        nseq=int(series.loc[usable].astype(str).nunique())
    levels: list[str]=[]
    if state_col in data.columns and not _is_list_column(data[state_col]):
        s=data[state_col]; usable=~_missing_mask(s)
        if isinstance(s.dtype,pd.CategoricalDtype): levels=[str(x) for x in s.cat.categories]
        else: levels=list(dict.fromkeys(s.loc[usable].astype(str).tolist()))
    status=_status(audit)
    return ValidationResult(status in {"pass","review"},status,counts["error"],counts["review"],counts["info"],audit,_mapping(sequence_id_col,order_col,state_col,duration_col,metadata),len(data),nseq,levels)


def _stage_audit(audit: pd.DataFrame, stage: str) -> pd.DataFrame:
    if len(audit)==0:
        return pd.concat([pd.DataFrame({"stage":pd.Series(dtype="object")}),_empty_audit()],axis=1)
    out=audit.copy(); out.insert(0,"stage",stage); return out


def prepare_sequence_data(
    data: pd.DataFrame,
    sequence_id_col: str,
    order_col: str,
    state_col: str,
    duration_col: str | None = None,
    metadata_cols: Sequence[str] | None = None,
    expected_states: Sequence[Any] | None = None,
    missing_state_policy: str = "error",
    duplicate_position_policy: str = "error",
    repeated_state_policy: str = "preserve",
    zero_duration_policy: str = "preserve",
    unknown_state_policy: str = "preserve",
    unused_state_levels: str = "preserve",
) -> PrepareResult:
    choices={
        "missing_state_policy":{"error","drop"},
        "duplicate_position_policy":{"error","first","last"},
        "repeated_state_policy":{"preserve","collapse"},
        "zero_duration_policy":{"preserve","drop","error"},
        "unknown_state_policy":{"preserve","drop","error"},
        "unused_state_levels":{"preserve","drop"},
    }
    for name,allowed in choices.items():
        if locals()[name] not in allowed: raise ValidationError(f"`{name}` must be one of: {', '.join(sorted(allowed))}.")
    metadata=_normalize_cols(metadata_cols,"metadata_cols")
    initial=validate_sequence_data(data,sequence_id_col,order_col,state_col,duration_col,metadata,expected_states)
    input_audit=_stage_audit(initial.audit,"input")
    fatal={"duplicate_column_names","empty_data","missing_required_column","missing_metadata_column","invalid_sequence_id_type","invalid_state_type","invalid_order_type","missing_sequence_id","missing_sequence_order","non_finite_order","invalid_duration_type","negative_duration","non_finite_duration","invalid_metadata_type","inconsistent_metadata"}
    if initial.audit["issue_code"].isin(fatal).any():
        return PrepareResult(None,input_audit,_empty_decisions(),initial.mapping,"fail",len(data),0,[])

    working=data.copy(deep=True)
    working[".gp3_original_row"]=np.arange(1,len(working)+1,dtype=int)
    decisions=[]
    def decision(step:str,policy:str,affected:int,details:str)->None:
        decisions.append({"step":step,"policy":policy,"affected_rows":int(affected),"details":details})

    miss=_missing_mask(working[state_col])
    if missing_state_policy=="drop":
        affected=int(miss.sum()); working=working.loc[~miss].copy(); decision("missing_states","drop",affected,"Rows with missing or blank states were removed.")
    else: decision("missing_states","error",int(miss.sum()),"Missing states were retained as unresolved errors.")

    unknown=pd.Series(False,index=working.index)
    if expected_states is not None and len(working):
        expected={str(x) for x in expected_states}; unknown=(~_missing_mask(working[state_col])) & (~working[state_col].astype(str).isin(expected))
    if unknown_state_policy=="drop":
        affected=int(unknown.sum()); working=working.loc[~unknown].copy(); decision("unknown_states","drop",affected,"States absent from `expected_states` were removed.")
    else:
        details="Unknown states were "+("retained as unresolved errors." if unknown_state_policy=="error" else "preserved for review.")
        decision("unknown_states",unknown_state_policy,int(unknown.sum()),details)

    zero=pd.Series(False,index=working.index)
    if duration_col is not None and len(working):
        d=pd.to_numeric(working[duration_col],errors="coerce").astype(float); zero=working[duration_col].notna() & np.isfinite(d) & (d==0)
    if zero_duration_policy=="drop":
        affected=int(zero.sum()); working=working.loc[~zero].copy(); decision("zero_durations","drop",affected,"Rows with zero duration were removed.")
    else:
        details="Zero-duration rows were "+("retained as unresolved errors." if zero_duration_policy=="error" else "preserved.")
        decision("zero_durations",zero_duration_policy,int(zero.sum()),details)

    keys=list(zip(working[sequence_id_col].astype(str),working[order_col].map(_format_order_key),strict=True)) if len(working) else []
    if duplicate_position_policy in {"first","last"}:
        keep=pd.Series(True,index=working.index)
        if keys:
            if duplicate_position_policy=="first": keep=~pd.Series(keys,index=working.index).duplicated(keep="first")
            else: keep=~pd.Series(keys,index=working.index).duplicated(keep="last")
        affected=int((~keep).sum()); working=working.loc[keep].copy(); decision("duplicated_positions",duplicate_position_policy,affected,f"Duplicated positions were resolved by retaining the {duplicate_position_policy} occurrence.")
    else:
        s=pd.Series(keys); count=int(s.duplicated(False).sum()) if len(s) else 0
        decision("duplicated_positions","error",count,"Duplicated positions were retained as unresolved errors.")

    before=working.index.tolist()
    working=working.sort_values([sequence_id_col,order_col,".gp3_original_row"],kind="stable",na_position="last")
    moved=sum(a!=b for a,b in zip(before,working.index.tolist(),strict=True))
    working=working.reset_index(drop=True)
    decision("row_order","deterministic_sort",moved,"Rows were ordered by sequence identifier, sequence order, and original row.")

    collapsed=0
    if repeated_state_policy=="collapse" and len(working)>1:
        seqtxt=working[sequence_id_col].astype(str); statetxt=working[state_col].astype("string"); missing=_missing_mask(working[state_col])
        same=(seqtxt.eq(seqtxt.shift(1)) & ~missing & ~missing.shift(1,fill_value=True) & statetxt.eq(statetxt.shift(1))).fillna(False)
        group=(~same).cumsum()
        if duration_col is not None:
            for _,idxs in working.groupby(group,sort=False).groups.items():
                idxs=list(idxs)
                if len(idxs)>1:
                    vals=pd.to_numeric(working.loc[idxs,duration_col],errors="coerce")
                    working.loc[idxs[0],duration_col]=np.nan if vals.isna().all() else vals.sum(skipna=True)
        keep=~group.duplicated(); collapsed=int((~keep).sum()); working=working.loc[keep].reset_index(drop=True)
    decision("consecutive_repeats",repeated_state_policy,collapsed,"The first row was retained for each repeated run; available durations were summed." if repeated_state_policy=="collapse" else "Consecutive repeated states were preserved.")

    removed_levels=0
    if unused_state_levels=="drop" and isinstance(working[state_col].dtype,pd.CategoricalDtype):
        before=set(working[state_col].cat.categories); working[state_col]=working[state_col].cat.remove_unused_categories(); removed_levels=len(before-set(working[state_col].cat.categories))
    decision("unused_state_levels",unused_state_levels,removed_levels,"Unused factor levels were removed." if unused_state_levels=="drop" else "Unused factor levels were preserved.")

    source_mapped=[x for x in [sequence_id_col,order_col,state_col,duration_col] if x is not None]
    extras=[c for c in working.columns if c not in source_mapped+[".gp3_original_row"]]
    canonical_names=["sequence_id","sequence_order","state","original_row"]+(["duration"] if duration_col else [])
    collisions=[c for c in extras if c in canonical_names]
    if collisions: raise ValidationError("Unmapped source columns use reserved canonical names: "+", ".join(collisions)+".")
    canonical=pd.DataFrame({"sequence_id":working[sequence_id_col].values,"sequence_order":working[order_col].values,"state":working[state_col].values,"original_row":working[".gp3_original_row"].astype(int).values})
    if duration_col is not None: canonical["duration"]=working[duration_col].values
    for col in extras: canonical[col]=working[col].values
    decision("column_mapping","canonicalise",len(canonical),"Mapped columns were standardised while unmapped columns were preserved.")

    outval=validate_sequence_data(canonical,"sequence_id","sequence_order","state","duration" if duration_col else None,metadata,expected_states)
    final=outval.audit.copy(); policy=[]
    if zero_duration_policy=="error" and "duration" in canonical:
        vals=pd.to_numeric(canonical["duration"],errors="coerce"); rows=canonical["duration"].notna() & np.isfinite(vals) & (vals==0)
        for i in np.flatnonzero(rows.to_numpy()):
            policy.append(_issue(sequence_id=canonical.loc[i,"sequence_id"],row=int(canonical.loc[i,"original_row"]),column="duration",issue_code="zero_duration_disallowed",severity="error",value="0",message="Zero duration is disallowed by the selected policy.",action="Use `preserve`, `drop`, or correct the duration."))
    if unknown_state_policy=="error" and expected_states is not None:
        expected={str(x) for x in expected_states}; rows=(~_missing_mask(canonical["state"])) & (~canonical["state"].astype(str).isin(expected))
        for i in np.flatnonzero(rows.to_numpy()):
            policy.append(_issue(sequence_id=canonical.loc[i,"sequence_id"],row=int(canonical.loc[i,"original_row"]),column="state",issue_code="unknown_state_disallowed",severity="error",value=_value_text(canonical.loc[i,"state"]),message="The state is disallowed by the selected policy.",action="Use `preserve`, `drop`, or revise expected states."))
    if policy: final=_audit_frame(pd.concat([final,pd.DataFrame(policy)],ignore_index=True).to_dict("records"))
    combined=pd.concat([input_audit,_stage_audit(final,"output")],ignore_index=True)
    decisions_df=pd.DataFrame(decisions,columns=_DECISION_COLUMNS) if decisions else _empty_decisions()
    final_status=_status(final)
    if isinstance(canonical["state"].dtype,pd.CategoricalDtype): levels=[str(x) for x in canonical["state"].cat.categories]
    else: levels=list(dict.fromkeys(canonical.loc[~_missing_mask(canonical["state"]),"state"].astype(str).tolist()))
    return PrepareResult(None if final_status=="fail" else canonical,combined,decisions_df,initial.mapping,final_status,len(data),len(canonical),levels)
