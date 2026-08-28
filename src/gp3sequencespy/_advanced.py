from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np
import pandas as pd

from ._exceptions import ValidationError
from ._types import PrepareResult


def scalar_character(x: Any, argument: str, allow_none: bool = False) -> None:
    if allow_none and x is None: return
    if not isinstance(x,str) or not x: raise ValidationError(f"`{argument}` must be a single non-missing character value.")


def scalar_number(x: Any, argument: str, lower: float=-np.inf, upper: float=np.inf, integer: bool=False) -> None:
    valid=isinstance(x,(int,float,np.integer,np.floating)) and not isinstance(x,(bool,np.bool_)) and np.isfinite(x)
    if not valid or x<lower or x>upper or (integer and int(x)!=x): raise ValidationError(f"`{argument}` has an invalid numeric value.")


def scalar_logical(x: Any, argument: str) -> None:
    if not isinstance(x,(bool,np.bool_)): raise ValidationError(f"`{argument}` must be a single non-missing logical value.")


def match_cols(data: pd.DataFrame, columns: Sequence[str] | str | None, argument: str, allow_none: bool=True) -> list[str]:
    if allow_none and columns is None: return []
    if isinstance(columns,str): columns=[columns]
    if columns is None or not isinstance(columns,Sequence): raise ValidationError(f"`{argument}` must contain unique, non-missing column names.")
    cols=list(columns)
    if any(not isinstance(c,str) or not c for c in cols) or len(set(cols))!=len(cols): raise ValidationError(f"`{argument}` must contain unique, non-missing column names.")
    missing=[c for c in cols if c not in data.columns]
    if missing: raise ValidationError(f"Missing columns in `{argument}`: {', '.join(missing)}.")
    return cols


def adv_data(
    data: pd.DataFrame | PrepareResult | Any,
    sequence_id_col: str="sequence_id",
    order_col: str="sequence_order",
    state_col: str="state",
    metadata_cols: Sequence[str] | str | None=None,
    missing_state_policy: str="error",
    missing_state_label: str="<MISSING>",
) -> dict[str,Any]:
    if missing_state_policy not in {"error","drop","state"}: raise ValidationError("Invalid missing-state policy.")
    if missing_state_policy=="state": scalar_character(missing_state_label,"missing_state_label")
    if isinstance(data,PrepareResult): data=data.data
    elif not isinstance(data,pd.DataFrame) and hasattr(data,"data") and isinstance(data.data,pd.DataFrame): data=data.data
    if not isinstance(data,pd.DataFrame): raise ValidationError("`data` must be a data frame or an object with a data-frame `data` component.")
    scalar_character(sequence_id_col,"sequence_id_col"); scalar_character(order_col,"order_col"); scalar_character(state_col,"state_col")
    metadata=match_cols(data,metadata_cols,"metadata_cols")
    required=[sequence_id_col,order_col,state_col]
    overlap=[c for c in metadata if c in required]
    if overlap: raise ValidationError("`metadata_cols` must not repeat core sequence columns: "+", ".join(overlap)+".")
    missing=[c for c in required if c not in data.columns]
    if missing: raise ValidationError("Missing required sequence columns: "+", ".join(missing)+".")
    if len(data)==0: raise ValidationError("`data` must contain at least one sequence row.")
    if data.columns.duplicated().any(): raise ValidationError("`data` contains duplicated column names.")
    ident=data[sequence_id_col]; order=data[order_col]; state=data[state_col]
    if ident.map(lambda x:isinstance(x,(list,dict,set,tuple,np.ndarray)) if x is not None else False).any() or state.map(lambda x:isinstance(x,(list,dict,set,tuple,np.ndarray)) if x is not None else False).any():
        raise ValidationError("Sequence identifiers and states must be atomic vectors.")
    if not pd.api.types.is_numeric_dtype(order.dtype) or order.isna().any() or not np.isfinite(pd.to_numeric(order)).all():
        raise ValidationError("The sequence order column must contain finite, non-missing numeric values.")
    id_text=ident.astype("string"); state_text=state.astype("string")
    missing_id=ident.isna() | id_text.str.strip().eq("").fillna(False)
    if missing_id.any(): raise ValidationError("Sequence identifiers must not be missing or blank.")
    missing_state=state.isna() | state_text.str.strip().eq("").fillna(False)
    if missing_state_policy=="error" and missing_state.any(): raise ValidationError("Missing states were found. Select an explicit non-error policy to continue.")
    working=data.copy(); working[".gp3_adv_original_row"]=np.arange(1,len(working)+1)
    if missing_state_policy=="drop": working=working.loc[~missing_state].copy()
    elif missing_state_policy=="state":
        vals=working[state_col].astype("string").copy(); vals.loc[missing_state]=missing_state_label; working[state_col]=vals.astype(object)
    if len(working)==0: raise ValidationError("No sequence rows remain after applying the missing-state policy.")
    key=working[sequence_id_col].astype(str)+"\x1c"+working[order_col].map(lambda v:format(float(v),".17g"))
    if key.duplicated().any(): raise ValidationError("Duplicated sequence positions were found. Prepare the data before advanced analysis.")
    working=working.sort_values([sequence_id_col,order_col,".gp3_adv_original_row"],kind="stable").reset_index(drop=True)
    seq_ids=list(dict.fromkeys(working[sequence_id_col].astype(str).tolist()))
    sequences={sid:working.loc[working[sequence_id_col].astype(str)==sid,state_col].astype(str).tolist() for sid in seq_ids}
    orders={sid:working.loc[working[sequence_id_col].astype(str)==sid,order_col].tolist() for sid in seq_ids}
    observed=list(dict.fromkeys(working[state_col].astype(str).tolist()))
    if isinstance(working[state_col].dtype,pd.CategoricalDtype): state_levels=[str(x) for x in working[state_col].cat.categories if str(x) in observed]
    else: state_levels=sorted(observed)
    metadata_df=None
    if metadata:
        rows=[]
        for sid in seq_ids:
            part=working.loc[working[sequence_id_col].astype(str)==sid]
            for c in metadata:
                vals=part[c].astype("string").fillna("<NA>")
                if vals.nunique(dropna=False)>1: raise ValidationError(f"Metadata vary within sequence `{sid}`: {c}.")
            rec={sequence_id_col:sid,**{c:part.iloc[0][c] for c in metadata}}; rows.append(rec)
        metadata_df=pd.DataFrame(rows)
    return {"data":working,"sequences":sequences,"orders":orders,"sequence_ids":seq_ids,"state_levels":state_levels,"metadata":metadata_df,"columns":{"sequence_id":sequence_id_col,"order":order_col,"state":state_col,"metadata":metadata}}


def group_key(data: pd.DataFrame, group_cols: Sequence[str]) -> pd.Series:
    if not group_cols: return pd.Series(["__all__"]*len(data),index=data.index,dtype=object)
    vals=[]
    for c in group_cols: vals.append(data[c].astype("string").fillna("<NA>"))
    out=vals[0].astype(str)
    for v in vals[1:]: out=out+"\x1d"+v.astype(str)
    return out


def state_order(values: Sequence[Any] | pd.Series, state_levels: Sequence[Any] | None=None) -> list[str]:
    vals=pd.Series(list(values)); observed=list(dict.fromkeys(vals.dropna().astype(str).tolist()))
    if state_levels is None: return sorted(observed)
    levels=[str(x) for x in state_levels]
    if any(not x.strip() for x in levels) or len(set(levels))!=len(levels): raise ValidationError("`state_levels` must contain unique, non-missing, non-blank values.")
    return [x for x in levels if x in observed]+sorted([x for x in observed if x not in levels])


def tie(states: Sequence[str], weights: Sequence[float], levels: Sequence[str], tie_method: str) -> dict[str,Any]:
    totals: dict[str,float]={}
    for s,w in zip(states,weights,strict=True): totals[s]=totals.get(s,0.0)+float(w)
    max_total=max(totals.values()); eps=np.sqrt(np.finfo(float).eps)
    tied=[s for s,v in totals.items() if abs(v-max_total)<=eps]; ordered=state_order(tied,levels)
    if tie_method=="first": selected=ordered[0]
    elif tie_method=="last": selected=ordered[-1]
    elif tie_method=="missing": selected=ordered[0] if len(ordered)==1 else None
    elif tie_method=="all": selected=" | ".join(ordered)
    else: raise ValidationError("Invalid tie method.")
    return {"selected":selected,"tied":ordered,"total":max_total,"agreement":max_total/sum(weights)}


def edit_distance(a: Sequence[str],b: Sequence[str],indel_cost:float=1,substitution_cost:float=1,substitution_matrix: pd.DataFrame | np.ndarray | None=None,state_labels:Sequence[str]|None=None)->float:
    n,m=len(a),len(b); d=np.zeros((n+1,m+1),float); d[:,0]=np.arange(n+1)*indel_cost; d[0,:]=np.arange(m+1)*indel_cost
    if isinstance(substitution_matrix,np.ndarray):
        if state_labels is None: raise ValidationError("State labels are required with an unnamed substitution matrix.")
        substitution_matrix=pd.DataFrame(substitution_matrix,index=state_labels,columns=state_labels)
    for i in range(n):
        for j in range(m):
            if a[i]==b[j]: cost=0.0
            elif substitution_matrix is None: cost=float(substitution_cost)
            else:
                if a[i] not in substitution_matrix.index or b[j] not in substitution_matrix.columns: raise ValidationError("The substitution matrix does not cover all observed states.")
                cost=float(substitution_matrix.loc[a[i],b[j]])
            d[i+1,j+1]=min(d[i,j+1]+indel_cost,d[i+1,j]+indel_cost,d[i,j]+cost)
    return float(d[n,m])


def lcs_length(a:Sequence[str],b:Sequence[str])->int:
    m=len(b); prev=np.zeros(m+1,dtype=int)
    for x in a:
        cur=np.zeros(m+1,dtype=int)
        for j,y in enumerate(b,1): cur[j]=prev[j-1]+1 if x==y else max(prev[j],cur[j-1])
        prev=cur
    return int(prev[m])


def transition_profile(sequence:Sequence[str],states:Sequence[str],smoothing:float=0)->np.ndarray:
    p=len(states); idx={s:i for i,s in enumerate(states)}; out=np.full((p,p),float(smoothing))
    for a,b in zip(sequence[:-1],sequence[1:],strict=True): out[idx[a],idx[b]]+=1
    totals=out.sum(axis=1); nz=totals>0; out[nz]=out[nz]/totals[nz,None]
    return out.ravel()


def validate_distance_matrix(x: Any) -> tuple[np.ndarray,list[str]]:
    labels: list[str]
    if hasattr(x,"matrix") and hasattr(x,"labels"): mat=np.asarray(x.matrix,float); labels=list(x.labels)
    elif isinstance(x,pd.DataFrame): mat=x.to_numpy(float); labels=[str(v) for v in x.index]
    else: mat=np.asarray(x,float); labels=[str(i+1) for i in range(mat.shape[0])] if mat.ndim==2 else []
    if mat.ndim!=2 or mat.shape[0]!=mat.shape[1]: raise ValidationError("A square distance matrix is required.")
    if mat.shape[0]==0: raise ValidationError("The distance object must contain at least one sequence.")
    if not np.isfinite(mat).all() or (mat<0).any(): raise ValidationError("Sequence distances must be finite, non-missing, and non-negative.")
    tol=np.sqrt(np.finfo(float).eps)
    if np.max(np.abs(mat-mat.T))>tol: raise ValidationError("The distance matrix must be symmetric.")
    if np.max(np.abs(np.diag(mat)))>tol: raise ValidationError("The distance-matrix diagonal must be zero.")
    if len(set(labels))!=len(labels) or any(not s for s in labels): raise ValidationError("Distance rows and columns must have identical, unique sequence identifiers.")
    return mat,labels


def silhouette(assignments: Sequence[int], distance_matrix: np.ndarray) -> np.ndarray:
    labels=np.asarray(assignments); out=np.zeros(len(labels)); clusters=sorted(set(labels.tolist()))
    for i,own in enumerate(labels):
        same=np.flatnonzero(labels==own); same=same[same!=i]
        if len(same)==0: out[i]=0; continue
        a=float(distance_matrix[i,same].mean()); others=[float(distance_matrix[i,labels==k].mean()) for k in clusters if k!=own]; b=min(others) if others else 0
        out[i]=0 if max(a,b)==0 else (b-a)/max(a,b)
    return out


def row_normalise(x:np.ndarray,pseudocount:float=0)->np.ndarray:
    x=np.asarray(x,float)+pseudocount; totals=x.sum(axis=1); bad=(totals<=0)|(~np.isfinite(totals)); x[bad]=1; return x/x.sum(axis=1,keepdims=True)


def vector_normalise(x:np.ndarray,pseudocount:float=0)->np.ndarray:
    x=np.asarray(x,float)+pseudocount; total=x.sum();
    if not np.isfinite(total) or total<=0: x=np.ones_like(x)
    return x/x.sum()


def forward_backward(obs:np.ndarray,initial:np.ndarray,transition:np.ndarray,emission:np.ndarray)->dict[str,Any]:
    n_states=len(initial); n=len(obs); alpha=np.zeros((n,n_states)); scales=np.zeros(n)
    alpha[0]=initial*emission[:,obs[0]]; scales[0]=alpha[0].sum(); scales[0]=np.finfo(float).tiny if not np.isfinite(scales[0]) or scales[0]<=0 else scales[0]; alpha[0]/=scales[0]
    for t in range(1,n):
        alpha[t]=(alpha[t-1]@transition)*emission[:,obs[t]]; scales[t]=alpha[t].sum(); scales[t]=np.finfo(float).tiny if not np.isfinite(scales[t]) or scales[t]<=0 else scales[t]; alpha[t]/=scales[t]
    beta=np.ones((n,n_states))
    for t in range(n-2,-1,-1): beta[t]=transition@(emission[:,obs[t+1]]*beta[t+1]); beta[t]/=scales[t+1]
    gamma=alpha*beta; gt=gamma.sum(axis=1); bad=(~np.isfinite(gt))|(gt<=0); gamma[bad]=1/n_states; gt[bad]=1; gamma/=gt[:,None]
    xi=np.zeros((max(n-1,0),n_states,n_states))
    for t in range(n-1):
        cur=np.outer(alpha[t],emission[:,obs[t+1]]*beta[t+1])*transition; total=cur.sum(); xi[t]=cur/total if total>0 else cur
    return {"alpha":alpha,"beta":beta,"gamma":gamma,"xi":xi,"log_likelihood":float(np.log(scales).sum())}


def viterbi(obs:np.ndarray,initial:np.ndarray,transition:np.ndarray,emission:np.ndarray)->dict[str,Any]:
    ni=np.log(np.maximum(initial,np.finfo(float).tiny)); nt=np.log(np.maximum(transition,np.finfo(float).tiny)); ne=np.log(np.maximum(emission,np.finfo(float).tiny)); n=len(obs); k=len(initial)
    delta=np.full((n,k),-np.inf); psi=np.zeros((n,k),int); delta[0]=ni+ne[:,obs[0]]
    for t in range(1,n):
        for j in range(k):
            cand=delta[t-1]+nt[:,j]; psi[t,j]=int(np.argmax(cand)); delta[t,j]=cand[psi[t,j]]+ne[j,obs[t]]
    path=np.zeros(n,int); path[-1]=int(np.argmax(delta[-1]));
    for t in range(n-2,-1,-1): path[t]=psi[t+1,path[t+1]]
    return {"path":path,"log_probability":float(delta[-1,path[-1]])}
