from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np
import pandas as pd

from ._exceptions import ValidationError
from ._types import EncodingResult, PathFormatResult, StateSummaryResult, TransitionSummaryResult
from .data import _missing_mask, _normalize_cols, validate_sequence_data


def _assert_text_scalar(value: Any, argument: str) -> None:
    if not isinstance(value,str) or not value:
        raise ValidationError(f"`{argument}` must be one non-missing, non-empty character value.")


def _assert_flag(value: Any, argument: str) -> None:
    if not isinstance(value,(bool,np.bool_)):
        raise ValidationError(f"`{argument}` must be either `TRUE` or `FALSE`.")


def _assert_output_names(metadata_cols: Sequence[str] | None, reserved: Sequence[str], context: str) -> list[str]:
    cols=_normalize_cols(metadata_cols,"metadata_cols")
    collisions=[x for x in cols if x in reserved]
    if collisions:
        raise ValidationError(f"Metadata column names conflict with {context} output columns: {', '.join(collisions)}.")
    return cols


def _summary_input(
    data: pd.DataFrame,
    sequence_id_col: str,
    order_col: str,
    state_col: str,
    duration_col: str | None = None,
    metadata_cols: Sequence[str] | None = None,
    expected_states: Sequence[Any] | None = None,
) -> dict[str,Any]:
    metadata=_normalize_cols(metadata_cols,"metadata_cols")
    val=validate_sequence_data(data,sequence_id_col,order_col,state_col,duration_col,metadata,expected_states)
    if not val.valid:
        codes=list(dict.fromkeys(val.audit.loc[val.audit["severity"]=="error","issue_code"].tolist()))
        raise ValidationError("Sequence data failed validation: "+", ".join(codes)+". Resolve the errors or use `prepare_sequence_data()` with explicit policies before continuing.")
    reserved={"sequence_id","sequence_order","state","original_row","duration"}
    _assert_output_names(metadata,reserved,"canonical")
    working=data.copy()
    working["__original_row"]=np.arange(1,len(working)+1,dtype=int)
    # R sorts numeric/logical IDs numerically; character/factor lexically.
    sort_seq=working[sequence_id_col]
    if not pd.api.types.is_numeric_dtype(sort_seq.dtype): sort_seq=sort_seq.astype(str)
    working=working.assign(__seq_sort=sort_seq).sort_values(["__seq_sort",order_col,"__original_row"],kind="stable").drop(columns="__seq_sort").reset_index(drop=True)
    canonical=pd.DataFrame({
        "sequence_id":working[sequence_id_col].astype(str),
        "sequence_order":working[order_col].values,
        "state":working[state_col].astype(str).values,
        "original_row":working["__original_row"].astype(int).values,
    })
    if duration_col is not None: canonical["duration"]=working[duration_col].values
    for col in metadata: canonical[col]=working[col].values
    original_levels=[str(x) for x in data[state_col].cat.categories] if isinstance(data[state_col].dtype,pd.CategoricalDtype) else None
    return {"data":canonical,"audit":val.audit,"status":val.status,"mapping":val.mapping,"original_state_levels":original_levels}


def encode_sequence_data(
    data: pd.DataFrame,
    sequence_id_col: str,
    order_col: str,
    state_col: str,
    duration_col: str | None = None,
    metadata_cols: Sequence[str] | None = None,
    expected_states: Sequence[Any] | None = None,
    state_levels: Sequence[Any] | None = None,
    prefix: str = "S",
    width: int | None = None,
) -> EncodingResult:
    """Create deterministic state integer and labelled encodings."""
    _assert_text_scalar(prefix,"prefix")
    inp=_summary_input(data,sequence_id_col,order_col,state_col,duration_col,metadata_cols,expected_states)
    metadata=_assert_output_names(metadata_cols,["state_index","state_code"],"encoded")
    observed=list(dict.fromkeys(inp["data"]["state"].tolist()))
    if state_levels is None:
        resolved=inp["original_state_levels"] if inp["original_state_levels"] is not None else sorted(observed)
    else:
        if isinstance(state_levels,(str,bytes)):
            state_levels=[state_levels]
        resolved=[str(x) for x in state_levels]
        if any(x is None or not str(x).strip() for x in state_levels) or len(set(resolved))!=len(resolved):
            raise ValidationError("`state_levels` must contain unique, non-empty values.")
        omitted=[x for x in observed if x not in resolved]
        if omitted: raise ValidationError("`state_levels` omits observed states: "+", ".join(omitted)+".")
    if width is None: resolved_width=max(1,len(str(len(resolved))))
    else:
        if isinstance(width,bool) or not isinstance(width,(int,np.integer,float,np.floating)) or not np.isfinite(width) or width<1 or int(width)!=width:
            raise ValidationError("`width` must be one positive whole number.")
        resolved_width=int(width)
    dictionary=pd.DataFrame({
        "state":resolved,
        "state_index":np.arange(1,len(resolved)+1,dtype=int),
        "state_code":[f"{prefix}{i:0{resolved_width}d}" for i in range(1,len(resolved)+1)],
        "observed":[x in observed for x in resolved],
    })
    encoded=inp["data"].copy()
    idx=dict(zip(dictionary.state,dictionary.state_index,strict=True)); codes=dict(zip(dictionary.state,dictionary.state_code,strict=True))
    encoded["state_index"]=encoded["state"].map(idx).astype(int)
    encoded["state_code"]=encoded["state"].map(codes)
    front=["sequence_id","sequence_order","state","state_index","state_code","original_row"]
    encoded=encoded[front+[c for c in encoded.columns if c not in front]]
    return EncodingResult(encoded,dictionary,inp["mapping"],inp["status"],inp["audit"],resolved,{"prefix":prefix,"width":resolved_width})


def _meta_values(df:pd.DataFrame,rows:list[int],metadata:list[str])->dict[str,Any]:
    out={}
    for c in metadata:
        vals=df.loc[rows,c]
        usable=vals.loc[~vals.isna()]
        out[c]=usable.iloc[0] if len(usable) else vals.iloc[0]
    return out


def _sum_or_na(s:pd.Series)->float:
    return float("nan") if len(s)==0 or s.isna().all() else float(pd.to_numeric(s,errors="coerce").sum(skipna=True))


def _mean_or_na(s:pd.Series)->float:
    return float("nan") if len(s)==0 or s.isna().all() else float(pd.to_numeric(s,errors="coerce").mean(skipna=True))


def _safe_prop(num:float,den:float)->float:
    return float("nan") if pd.isna(den) or den==0 else float(num/den)


def summarise_sequence_states(
    data: pd.DataFrame,
    sequence_id_col: str,
    order_col: str,
    state_col: str,
    duration_col: str | None = None,
    metadata_cols: Sequence[str] | None = None,
    expected_states: Sequence[Any] | None = None,
) -> StateSummaryResult:
    metadata=_assert_output_names(metadata_cols,["state","n_observations","observation_proportion","duration_sum","duration_proportion","mean_duration"],"state-summary")
    inp=_summary_input(data,sequence_id_col,order_col,state_col,duration_col,metadata,expected_states); df=inp["data"]
    ids=list(dict.fromkeys(df.sequence_id.tolist())); include_duration="duration" in df
    seq_rows=[]
    for sid in ids:
        rows=df.index[df.sequence_id==sid].tolist(); meta=_meta_values(df,rows,metadata); states=df.loc[rows,"state"].tolist(); state_order=list(dict.fromkeys(states)); n=len(rows)
        seq_duration=_sum_or_na(df.loc[rows,"duration"]) if include_duration else None
        for st in state_order:
            sr=[i for i in rows if df.loc[i,"state"]==st]
            rec={"sequence_id":sid,**meta,"state":st,"n_observations":len(sr),"observation_proportion":len(sr)/n}
            if include_duration:
                sd=_sum_or_na(df.loc[sr,"duration"]); rec.update(duration_sum=sd,duration_proportion=_safe_prop(sd,seq_duration),mean_duration=_mean_or_na(df.loc[sr,"duration"]))
            seq_rows.append(rec)
    by=pd.DataFrame(seq_rows)
    overall=[]; total_obs=len(df); total_seq=len(ids); total_dur=_sum_or_na(df.duration) if include_duration else None
    for st in list(dict.fromkeys(df.state.tolist())):
        sr=df.index[df.state==st].tolist(); sids=list(dict.fromkeys(df.loc[sr,"sequence_id"].tolist()))
        rec={"state":st,"n_sequences":len(sids),"sequence_proportion":len(sids)/total_seq,"n_observations":len(sr),"observation_proportion":len(sr)/total_obs}
        if include_duration:
            sd=_sum_or_na(df.loc[sr,"duration"]); rec.update(duration_sum=sd,duration_proportion=_safe_prop(sd,total_dur),mean_duration=_mean_or_na(df.loc[sr,"duration"]))
        overall.append(rec)
    return StateSummaryResult(by,pd.DataFrame(overall),inp["audit"],inp["status"],inp["mapping"])


def summarise_sequence_transitions(
    data: pd.DataFrame,
    sequence_id_col: str,
    order_col: str,
    state_col: str,
    metadata_cols: Sequence[str] | None = None,
    expected_states: Sequence[Any] | None = None,
    include_self: bool = True,
) -> TransitionSummaryResult:
    _assert_flag(include_self,"include_self")
    metadata=_assert_output_names(metadata_cols,["from_state","to_state","n_transitions","sequence_transition_proportion","transition_proportion","origin_transition_proportion","n_sequences","sequence_proportion"],"transition-summary")
    inp=_summary_input(data,sequence_id_col,order_col,state_col,None,metadata,expected_states); df=inp["data"]; ids=list(dict.fromkeys(df.sequence_id.tolist()))
    by_rows=[]; raw=[]
    for sid in ids:
        rows=df.index[df.sequence_id==sid].tolist()
        if len(rows)<2: continue
        states=df.loc[rows,"state"].tolist(); pairs=list(zip(states[:-1],states[1:],strict=True))
        if not include_self: pairs=[p for p in pairs if p[0]!=p[1]]
        if not pairs: continue
        raw.extend({"sequence_id":sid,"from_state":a,"to_state":b} for a,b in pairs)
        meta=_meta_values(df,rows,metadata); unique=list(dict.fromkeys(pairs)); total=len(pairs)
        for a,b in unique:
            count=sum(p==(a,b) for p in pairs); origin=sum(p[0]==a for p in pairs)
            by_rows.append({"sequence_id":sid,**meta,"from_state":a,"to_state":b,"n_transitions":count,"sequence_transition_proportion":count/total,"origin_transition_proportion":count/origin})
    rawdf=pd.DataFrame(raw,columns=["sequence_id","from_state","to_state"])
    overall=[]
    if len(rawdf):
        pairs=list(dict.fromkeys(zip(rawdf.from_state,rawdf.to_state,strict=True))); total=len(rawdf); total_seq=len(ids)
        for a,b in pairs:
            mask=(rawdf.from_state==a)&(rawdf.to_state==b); count=int(mask.sum()); origin=int((rawdf.from_state==a).sum()); contrib=rawdf.loc[mask,"sequence_id"].nunique()
            overall.append({"from_state":a,"to_state":b,"n_sequences":int(contrib),"sequence_proportion":contrib/total_seq,"n_transitions":count,"transition_proportion":count/total,"origin_transition_proportion":count/origin})
    return TransitionSummaryResult(pd.DataFrame(by_rows),pd.DataFrame(overall),inp["audit"],inp["status"],inp["mapping"],include_self)


def format_sequence_paths(
    data: pd.DataFrame,
    sequence_id_col: str,
    order_col: str,
    state_col: str,
    metadata_cols: Sequence[str] | None = None,
    expected_states: Sequence[Any] | None = None,
    separator: str = " > ",
    collapse_repeats: bool = False,
) -> PathFormatResult:
    _assert_text_scalar(separator,"separator"); _assert_flag(collapse_repeats,"collapse_repeats")
    metadata=_assert_output_names(metadata_cols,["n_observations","n_states","n_unique_states","start_state","end_state","path"],"path")
    inp=_summary_input(data,sequence_id_col,order_col,state_col,None,metadata,expected_states); df=inp["data"]
    rows=[]
    for sid in list(dict.fromkeys(df.sequence_id.tolist())):
        inds=df.index[df.sequence_id==sid].tolist(); observed=df.loc[inds,"state"].tolist(); formatted=observed[:]
        if collapse_repeats: formatted=[x for i,x in enumerate(formatted) if i==0 or x!=formatted[i-1]]
        rows.append({"sequence_id":sid,**_meta_values(df,inds,metadata),"n_observations":len(observed),"n_states":len(formatted),"n_unique_states":len(dict.fromkeys(formatted)),"start_state":formatted[0],"end_state":formatted[-1],"path":separator.join(formatted)})
    return PathFormatResult(pd.DataFrame(rows),inp["audit"],inp["status"],inp["mapping"],{"separator":separator,"collapse_repeats":collapse_repeats})
