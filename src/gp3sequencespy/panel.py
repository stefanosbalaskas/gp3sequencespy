from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence
import numpy as np
import pandas as pd

from ._advanced import adv_data, scalar_character, scalar_logical
from ._exceptions import ValidationError
from .distances import compute_sequence_distance

@dataclass(slots=True)
class SequencePanel:
    data: pd.DataFrame
    index: pd.DataFrame
    sequences: dict[str,list[str]]
    orders: dict[str,list[Any]]
    state_levels: list[str]
    columns: dict[str,Any]
    settings: dict[str,Any]


def prepare_sequence_panel(data:Any,panel_id_col:str,occasion_col:str,sequence_id_col:str="sequence_id",order_col:str="sequence_order",state_col:str="state",metadata_cols:Sequence[str]|str|None=None,require_unique_occasions:bool=True)->SequencePanel:
    scalar_character(panel_id_col,"panel_id_col"); scalar_character(occasion_col,"occasion_col"); scalar_logical(require_unique_occasions,"require_unique_occasions")
    metadata=list(dict.fromkeys([panel_id_col,occasion_col]+(([metadata_cols] if isinstance(metadata_cols,str) else list(metadata_cols)) if metadata_cols is not None else [])))
    x=adv_data(data,sequence_id_col,order_col,state_col,metadata,"error"); meta=x["metadata"].copy(); pid=meta[panel_id_col]; occasion=meta[occasion_col]
    if (pid.isna()|pid.astype("string").str.strip().eq("")).any(): raise ValidationError("Panel identifiers must not be missing or blank.")
    if (occasion.isna()|occasion.astype("string").str.strip().eq("")).any(): raise ValidationError("Occasion values must not be missing or blank.")
    ptxt=pid.astype(str); otxt=occasion.astype(str); dup=ptxt+"\x1c"+otxt
    if require_unique_occasions and dup.duplicated(keep=False).any(): raise ValidationError("More than one sequence was found for panel/occasion combinations: "+", ".join(pd.unique(dup[dup.duplicated(keep=False)]))+".")
    ranks=np.zeros(len(meta),int)
    for p in pd.unique(ptxt):
        rows=np.flatnonzero(ptxt.to_numpy()==p); cur=occasion.iloc[rows]
        if pd.api.types.is_numeric_dtype(cur.dtype) or pd.api.types.is_datetime64_any_dtype(cur.dtype): order_idx=np.lexsort((meta.iloc[rows][sequence_id_col].astype(str).to_numpy(),pd.to_numeric(cur,errors="coerce").to_numpy()))
        elif isinstance(cur.dtype,pd.CategoricalDtype) and cur.dtype.ordered: order_idx=np.lexsort((meta.iloc[rows][sequence_id_col].astype(str).to_numpy(),cur.cat.codes.to_numpy()))
        else: order_idx=np.lexsort((meta.iloc[rows][sequence_id_col].astype(str).to_numpy(),cur.astype(str).to_numpy()))
        ranks[rows[order_idx]]=np.arange(1,len(rows)+1)
    lengths={sid:len(seq) for sid,seq in x["sequences"].items()}
    index=pd.DataFrame({"sequence_id":x["sequence_ids"],"panel_id":ptxt.tolist(),"occasion":otxt.tolist(),"occasion_rank":ranks.astype(int),"sequence_length":[lengths[s] for s in x["sequence_ids"]],"transition_count":[max(lengths[s]-1,0) for s in x["sequence_ids"]]})
    index=index.sort_values(["panel_id","occasion_rank","sequence_id"],kind="stable").reset_index(drop=True)
    return SequencePanel(x["data"],index,x["sequences"],x["orders"],x["state_levels"],{"panel_id":panel_id_col,"occasion":occasion_col,"sequence_id":sequence_id_col,"order":order_col,"state":state_col,"metadata":metadata},{"require_unique_occasions":bool(require_unique_occasions)})


def summarise_sequence_panel(panel:SequencePanel)->dict[str,Any]:
    if not isinstance(panel,SequencePanel): raise ValidationError("`panel` must be created by `prepare_sequence_panel()`.")
    idx=panel.index; occasion_levels=list(dict.fromkeys(idx.sort_values(["occasion_rank","occasion"],kind="stable").occasion.tolist())); orows=[]; srows=[]
    for occ in occasion_levels:
        cur=idx.loc[idx.occasion==occ]; orows.append({"occasion":occ,"n_panels":cur.panel_id.nunique(),"n_sequences":len(cur),"mean_length":float(cur.sequence_length.mean()),"median_length":float(cur.sequence_length.median()),"mean_transitions":float(cur.transition_count.mean())})
        seqs=[panel.sequences[s] for s in cur.sequence_id]
        total=sum(map(len,seqs))
        for st in panel.state_levels:
            oc=sum(seq.count(st) for seq in seqs); sc=sum(st in seq for seq in seqs); srows.append({"occasion":occ,"state":st,"occurrence_count":oc,"occurrence_share":oc/total if total else np.nan,"sequence_count":sc,"sequence_prevalence":sc/len(seqs) if seqs else np.nan})
    return {"occasions":pd.DataFrame(orows),"states":pd.DataFrame(srows),"n_panels":idx.panel_id.nunique(),"n_occasions":len(occasion_levels),"state_levels":panel.state_levels}


def compare_sequence_panel_changes(panel:SequencePanel,method:str="levenshtein",normalise:str="none",indel_cost:float=1,substitution_cost:float=1,substitution_matrix:Any=None,transition_smoothing:float=0)->pd.DataFrame:
    if not isinstance(panel,SequencePanel): raise ValidationError("`panel` must be created by `prepare_sequence_panel()`.")
    rows=[]; idx=panel.index
    for pid in pd.unique(idx.panel_id):
        cur=idx.loc[idx.panel_id==pid].sort_values(["occasion_rank","sequence_id"],kind="stable").reset_index(drop=True)
        for i in range(len(cur)-1):
            ids=cur.sequence_id.iloc[i:i+2].tolist(); subset=panel.data.loc[panel.data[panel.columns["sequence_id"]].astype(str).isin(ids)]
            d=compute_sequence_distance(subset,panel.columns["sequence_id"],panel.columns["order"],panel.columns["state"],method,indel_cost,substitution_cost,substitution_matrix,transition_smoothing,normalise)
            rows.append({"panel_id":pid,"from_sequence_id":ids[0],"to_sequence_id":ids[1],"from_occasion":cur.occasion.iloc[i],"to_occasion":cur.occasion.iloc[i+1],"from_rank":int(cur.occasion_rank.iloc[i]),"to_rank":int(cur.occasion_rank.iloc[i+1]),"distance":float(d.matrix[0,1]),"length_change":int(cur.sequence_length.iloc[i+1]-cur.sequence_length.iloc[i]),"transition_change":int(cur.transition_count.iloc[i+1]-cur.transition_count.iloc[i])})
    out=pd.DataFrame(rows,columns=["panel_id","from_sequence_id","to_sequence_id","from_occasion","to_occasion","from_rank","to_rank","distance","length_change","transition_change"]); out.attrs.update(gp3_class="gp3_sequence_panel_changes",method=method,normalise=normalise); return out


def plot_sequence_panel_changes(changes:pd.DataFrame,metric:str="distance",type:str="individual",ax=None,**kwargs):
    import matplotlib.pyplot as plt
    if not isinstance(changes,pd.DataFrame) or changes.attrs.get("gp3_class")!="gp3_sequence_panel_changes": raise ValidationError("`changes` must be created by `compare_sequence_panel_changes()`.")
    if metric not in {"distance","length_change","transition_change"}: raise ValidationError("Invalid metric.")
    if type not in {"individual","summary"}: raise ValidationError("Invalid type.")
    if changes.empty: raise ValidationError("There are no panel changes to plot.")
    ax=ax or plt.gca(); labels=(changes.from_occasion.astype(str)+" -> "+changes.to_occasion.astype(str)); levels=list(dict.fromkeys(changes.assign(_l=labels).sort_values(["from_rank","to_rank","_l"],kind="stable")._l)); x=labels.map({v:i+1 for i,v in enumerate(levels)}).to_numpy(); y=changes[metric].to_numpy(float)
    if type=="individual":
        for pid in pd.unique(changes.panel_id): idx=np.flatnonzero(changes.panel_id.to_numpy()==pid); ax.plot(x[idx],y[idx],marker='o',**kwargs)
    else:
        means=[]; ses=[]
        for lev in levels:
            z=changes.loc[labels==lev,metric].to_numpy(float); means.append(float(z.mean())); ses.append(float(z.std(ddof=1)/np.sqrt(len(z))) if len(z)>1 else 0)
        xx=np.arange(1,len(levels)+1); ax.errorbar(xx,means,yerr=ses,marker='o',**kwargs)
    ax.set_xticks(np.arange(1,len(levels)+1),levels); ax.set_xlabel("Occasion transition"); ax.set_ylabel(metric); return changes
