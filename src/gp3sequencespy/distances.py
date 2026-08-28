from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Sequence

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import cut_tree, linkage as scipy_linkage
from scipy.spatial.distance import squareform

from ._advanced import adv_data, edit_distance, lcs_length, scalar_number, silhouette, transition_profile, validate_distance_matrix
from ._exceptions import ValidationError
from ._types import SequenceDistanceResult


@dataclass(slots=True)
class SequenceClustering:
    assignments: pd.Series
    model: Any
    medoids: list[str]
    k: int
    method: str
    linkage: str | None
    distance: SequenceDistanceResult
    seed: int

    @property
    def cluster(self) -> pd.Series:
        return self.assignments


@dataclass(slots=True)
class SequenceClusterBootstrap:
    original: SequenceClustering
    pairwise_stability: pd.DataFrame
    evaluated_counts: pd.DataFrame
    iterations: pd.DataFrame
    overall: pd.DataFrame
    settings: dict[str, Any]


@dataclass(slots=True)
class SequenceClusterEnsemble:
    assignments: pd.Series
    coassociation: pd.DataFrame
    distance: SequenceDistanceResult
    model: Any
    source_assignments: list[pd.Series]
    k: int
    linkage: str


def _substitution_df(substitution_matrix: Any, states: Sequence[str]) -> pd.DataFrame | None:
    if substitution_matrix is None:
        return None
    if isinstance(substitution_matrix, pd.DataFrame):
        m = substitution_matrix.copy()
    else:
        a = np.asarray(substitution_matrix)
        if a.ndim != 2 or a.shape[0] != a.shape[1]:
            raise ValidationError("`substitution_matrix` must be a finite, non-negative, named square matrix.")
        raise ValidationError("An array substitution matrix must be supplied as a pandas DataFrame with state row/column names.")
    if m.shape[0] != m.shape[1] or list(m.index.astype(str)) == []:
        raise ValidationError("`substitution_matrix` must be a finite, non-negative, named square matrix.")
    m.index = m.index.astype(str); m.columns = m.columns.astype(str)
    arr = m.to_numpy(dtype=float)
    if not np.isfinite(arr).all() or (arr < 0).any() or m.index.has_duplicates or m.columns.has_duplicates or set(m.index) != set(m.columns):
        raise ValidationError("`substitution_matrix` must be a finite, non-negative, named square matrix.")
    missing = [s for s in states if s not in m.index]
    if missing:
        raise ValidationError("The substitution matrix does not cover all observed states: " + ", ".join(missing) + ".")
    m = m.loc[list(m.index), list(m.index)]
    tol = np.sqrt(np.finfo(float).eps)
    if np.max(np.abs(m.to_numpy() - m.to_numpy().T)) > tol:
        raise ValidationError("`substitution_matrix` must be symmetric for a sequence distance.")
    if np.max(np.abs(np.diag(m.to_numpy()))) > tol:
        raise ValidationError("The diagonal of `substitution_matrix` must be zero.")
    return m


def compute_sequence_distance(
    data: Any,
    sequence_id_col: str = "sequence_id",
    order_col: str = "sequence_order",
    state_col: str = "state",
    method: str = "levenshtein",
    indel_cost: float = 1,
    substitution_cost: float = 1,
    substitution_matrix: Any = None,
    transition_smoothing: float = 0,
    normalise: str = "none",
) -> SequenceDistanceResult:
    if method not in {"levenshtein", "lcs", "optimal_matching", "transition"}:
        raise ValidationError("Invalid distance method.")
    if normalise not in {"none", "max_length", "path_length"}:
        raise ValidationError("Invalid distance normalisation.")
    scalar_number(indel_cost, "indel_cost", lower=0)
    scalar_number(substitution_cost, "substitution_cost", lower=0)
    scalar_number(transition_smoothing, "transition_smoothing", lower=0)
    x = adv_data(data, sequence_id_col, order_col, state_col, missing_state_policy="error")
    ids = x["sequence_ids"]
    seqs = x["sequences"]
    n = len(ids)
    matrix = np.zeros((n, n), dtype=float)
    sub = _substitution_df(substitution_matrix, x["state_levels"])
    for i in range(n - 1):
        a = seqs[ids[i]]
        for j in range(i + 1, n):
            b = seqs[ids[j]]
            if method == "levenshtein":
                raw = edit_distance(a, b, 1, 1)
            elif method == "lcs":
                raw = len(a) + len(b) - 2 * lcs_length(a, b)
            elif method == "optimal_matching":
                raw = edit_distance(a, b, indel_cost, substitution_cost, sub)
            else:
                pa = transition_profile(a, x["state_levels"], transition_smoothing)
                pb = transition_profile(b, x["state_levels"], transition_smoothing)
                raw = float(np.sqrt(np.sum((pa - pb) ** 2)))
            den = 1.0
            if normalise == "max_length": den = float(max(len(a), len(b), 1))
            elif normalise == "path_length": den = float(max(len(a) + len(b), 1))
            matrix[i, j] = matrix[j, i] = float(raw) / den
    settings = {
        "indel_cost": indel_cost,
        "substitution_cost": substitution_cost,
        "substitution_matrix": sub,
        "transition_smoothing": transition_smoothing,
        "normalise": normalise,
    }
    return SequenceDistanceResult(matrix=matrix, labels=ids, method=method, normalise=normalise, settings=settings, sequences=x["data"].drop(columns=[".gp3_adv_original_row"], errors="ignore"))


def summarise_sequence_distance(distance: Any) -> dict[str, Any]:
    m, ids = validate_distance_matrix(distance)
    vals = m[np.triu_indices(len(ids), 1)] if len(ids) > 1 else np.array([], float)
    overall = pd.DataFrame([{
        "n_sequences": len(ids), "n_pairs": len(vals),
        "mean_distance": float(vals.mean()) if len(vals) else np.nan,
        "median_distance": float(np.median(vals)) if len(vals) else np.nan,
        "min_distance": float(vals.min()) if len(vals) else np.nan,
        "max_distance": float(vals.max()) if len(vals) else np.nan,
    }])
    rows=[]
    for i,sid in enumerate(ids):
        v=np.delete(m[i],i)
        rows.append({"sequence_id":sid,"mean_distance":float(v.mean()) if len(v) else np.nan,"median_distance":float(np.median(v)) if len(v) else np.nan,"min_distance":float(v.min()) if len(v) else np.nan,"max_distance":float(v.max()) if len(v) else np.nan})
    return {"overall":overall,"per_sequence":pd.DataFrame(rows),"method":getattr(distance,"method",None),"settings":getattr(distance,"settings",None)}


def _hierarchical(m: np.ndarray, ids: list[str], k: int, linkage: str) -> tuple[pd.Series, Any, list[str]]:
    mapping={"ward.D":"ward","ward.D2":"ward","single":"single","complete":"complete","average":"average","median":"median","centroid":"centroid","mcquitty":"weighted"}
    z=scipy_linkage(squareform(m,checks=False),method=mapping[linkage])
    labels=cut_tree(z,n_clusters=[k]).reshape(-1)+1
    assignments=pd.Series(labels,index=ids,dtype=int)
    med=[]
    for c in sorted(assignments.unique()):
        idx=np.flatnonzero(assignments.to_numpy()==c)
        scores=m[np.ix_(idx,idx)].sum(axis=1)
        best=idx[int(np.argmin(scores))]
        med.append(ids[best])
    return assignments,z,med


def _pam(m: np.ndarray, ids: list[str], k: int) -> tuple[pd.Series, dict[str,Any], list[str]]:
    # Deterministic BUILD + SWAP PAM. Tie-breaking follows input identifier order.
    n=len(ids)
    total=m.sum(axis=1)
    medoids=[int(np.argmin(total))]
    while len(medoids)<k:
        nearest=np.min(m[:,medoids],axis=1)
        best_gain=-np.inf; best=None
        for h in range(n):
            if h in medoids: continue
            gain=float(np.maximum(0,nearest-m[:,h]).sum())
            if gain>best_gain+1e-15 or (abs(gain-best_gain)<=1e-15 and (best is None or h<best)):
                best_gain=gain; best=h
        medoids.append(int(best))
    def objective(ms:list[int])->float:
        return float(np.min(m[:,ms],axis=1).sum())
    current=objective(medoids)
    improved=True
    while improved:
        improved=False; best_obj=current; best_swap=None
        for pos,old in enumerate(medoids):
            for h in range(n):
                if h in medoids: continue
                trial=medoids.copy(); trial[pos]=h
                val=objective(trial)
                key=(pos,h)
                if val<best_obj-1e-12 or (abs(val-best_obj)<=1e-12 and best_swap is not None and key<best_swap):
                    best_obj=val; best_swap=key
        if best_swap is not None and best_obj<current-1e-12:
            medoids[best_swap[0]]=best_swap[1]; current=best_obj; improved=True
    # Stable canonical cluster numbering by medoid index.
    medoids=sorted(medoids)
    d=m[:,medoids]
    lab=np.argmin(d,axis=1)+1
    assignments=pd.Series(lab,index=ids,dtype=int)
    return assignments,{"medoid_indices":medoids,"objective":current},[ids[i] for i in medoids]


def _clara(m:np.ndarray,ids:list[str],k:int,seed:int,n_samples:int=5,sample_size:int|None=None)->tuple[pd.Series,dict[str,Any],list[str]]:
    n=len(ids); rng=np.random.default_rng(seed)
    if sample_size is None: sample_size=min(n,max(40+2*k,k+1))
    sample_size=max(k+1,min(n,int(sample_size)))
    best=None
    for b in range(max(1,int(n_samples))):
        sel=np.arange(n) if sample_size==n else np.sort(rng.choice(n,sample_size,replace=False))
        sub_ids=[ids[i] for i in sel]
        _,model,submed=_pam(m[np.ix_(sel,sel)],sub_ids,k)
        med_idx=[ids.index(x) for x in submed]
        obj=float(np.min(m[:,med_idx],axis=1).sum())
        candidate=(obj,med_idx,b)
        if best is None or candidate[:2]<best[:2]: best=candidate
    med_idx=sorted(best[1]); labels=np.argmin(m[:,med_idx],axis=1)+1
    return pd.Series(labels,index=ids,dtype=int),{"objective":best[0],"sample_iteration":best[2]},[ids[i] for i in med_idx]


def _distance_result_from_matrix(m:np.ndarray,ids:list[str],source:Any=None)->SequenceDistanceResult:
    return SequenceDistanceResult(matrix=m.copy(),labels=list(ids),method=getattr(source,"method","precomputed"),normalise=getattr(source,"normalise","none"),settings=getattr(source,"settings",{}))


def cluster_sequences(distance: Any, k: int, method: str="hierarchical", linkage: str="average", seed: int=1, **kwargs: Any) -> SequenceClustering:
    if method not in {"hierarchical","pam","clara"}: raise ValidationError("Invalid clustering method.")
    scalar_number(k,"k",lower=2,integer=True); scalar_number(seed,"seed",lower=0,integer=True)
    allowed={"ward.D","ward.D2","single","complete","average","mcquitty","median","centroid"}
    if linkage not in allowed: raise ValidationError("`linkage` is not a supported `stats::hclust()` method.")
    m,ids=validate_distance_matrix(distance); n=len(ids)
    if k>=n: raise ValidationError("`k` must be smaller than the number of sequences.")
    if any(x in kwargs for x in {"x","k","diss","metric"}): raise ValidationError("Do not supply protected clustering arguments through `...`.")
    if method=="hierarchical":
        unexpected=set(kwargs)-{"members"}
        if unexpected: raise ValidationError("Unsupported hierarchical clustering arguments: "+", ".join(sorted(unexpected))+".")
        a,model,med=_hierarchical(m,ids,int(k),linkage)
    elif method=="pam":
        a,model,med=_pam(m,ids,int(k))
    else:
        a,model,med=_clara(m,ids,int(k),int(seed),int(kwargs.pop("samples",5)),kwargs.pop("sampsize",None))
        if kwargs: raise ValidationError("Unsupported CLARA clustering arguments: "+", ".join(sorted(kwargs))+".")
    return SequenceClustering(a,model,med,int(k),method,linkage if method=="hierarchical" else None,_distance_result_from_matrix(m,ids,distance),int(seed))


def _assignments_and_distance(clustering: Any, distance: Any=None)->tuple[pd.Series,np.ndarray,list[str]]:
    if isinstance(clustering,(SequenceClustering,SequenceClusterEnsemble)):
        a=clustering.assignments.copy(); m,ids=validate_distance_matrix(clustering.distance)
    else:
        if not isinstance(clustering,pd.Series): raise ValidationError("Cluster assignments must be a named pandas Series.")
        a=clustering.copy(); m,ids=validate_distance_matrix(distance)
    a.index=a.index.astype(str)
    if a.index.has_duplicates or a.index.isna().any() or any(not str(x) for x in a.index): raise ValidationError("Cluster assignments must have unique sequence-ID names.")
    if set(a.index)!=set(ids): raise ValidationError("Assignment names and distance-matrix identifiers must match.")
    a=a.reindex(ids)
    if a.isna().any() or a.nunique()<2: raise ValidationError("At least two non-missing clusters are required.")
    return a,m,ids


def validate_sequence_clusters(clustering: Any, distance: Any=None)->dict[str,pd.DataFrame]:
    a,m,ids=_assignments_and_distance(clustering,distance); arr=a.to_numpy(); sil=silhouette(arr,m); clusters=sorted(pd.unique(arr).tolist(),key=str)
    sizes={c:int((arr==c).sum()) for c in clusters}; within=[]; between=[]
    for i in range(len(ids)-1):
        for j in range(i+1,len(ids)):
            (within if arr[i]==arr[j] else between).append(float(m[i,j]))
    max_intra=max(within,default=0); min_inter=min(between,default=np.inf)
    dunn=min_inter/max_intra if max_intra>0 and np.isfinite(min_inter) else np.nan
    ratio=float(np.mean(within)/np.mean(between)) if within and between and np.mean(between)>0 else np.nan
    overall=pd.DataFrame([{"n_sequences":len(ids),"n_clusters":len(clusters),"average_silhouette":float(np.mean(sil)),"minimum_silhouette":float(np.min(sil)),"dunn_index":dunn,"within_between_ratio":ratio,"singleton_clusters":sum(v==1 for v in sizes.values())}])
    per=pd.DataFrame({"sequence_id":ids,"cluster":[str(x) for x in arr],"silhouette":sil.astype(float)})
    size=pd.DataFrame({"cluster":[str(x) for x in clusters],"size":[sizes[x] for x in clusters]})
    return {"overall":overall,"cluster_sizes":size,"per_sequence":per}


def extract_representative_sequences(clustering: Any,distance: Any=None,n_per_cluster:int=1)->pd.DataFrame:
    scalar_number(n_per_cluster,"n_per_cluster",lower=1,integer=True); a,m,ids=_assignments_and_distance(clustering,distance); arr=a.to_numpy(); rows=[]
    for c in sorted(pd.unique(arr).tolist(),key=str):
        idx=np.flatnonzero(arr==c); scores=np.array([0.0]) if len(idx)==1 else m[np.ix_(idx,idx)].sum(axis=1)/(len(idx)-1)
        order=sorted(range(len(idx)),key=lambda q:(scores[q],ids[idx[q]]))[:int(n_per_cluster)]
        for rank,q in enumerate(order,1): rows.append({"cluster":str(c),"rank":rank,"sequence_id":ids[idx[q]],"mean_within_distance":float(scores[q])})
    return pd.DataFrame(rows)


def bootstrap_sequence_clusters(distance:Any,k:int,method:str="hierarchical",n_boot:int=100,sample_fraction:float=.8,seed:int=1,linkage:str="average",**kwargs:Any)->SequenceClusterBootstrap:
    scalar_number(k,"k",lower=2,integer=True); scalar_number(n_boot,"n_boot",lower=1,integer=True); scalar_number(sample_fraction,"sample_fraction",.2,1); scalar_number(seed,"seed",lower=0,integer=True)
    m,ids=validate_distance_matrix(distance); n=len(ids); sample_n=max(int(k)+1,int(np.floor(n*sample_fraction)))
    if sample_n>n: raise ValidationError("The requested subsample is too small for `k`.")
    original=cluster_sequences(distance,k,method,linkage,seed,**kwargs); orig=original.assignments.to_numpy(); orig_same=orig[:,None]==orig[None,:]
    evaluated=np.zeros((n,n),int); matched=np.zeros((n,n),int); rows=[]; rng=np.random.default_rng(seed)
    for b in range(1,int(n_boot)+1):
        selected=np.sort(rng.choice(n,sample_n,replace=False)); sub=m[np.ix_(selected,selected)]; sids=[ids[i] for i in selected]
        subd=_distance_result_from_matrix(sub,sids,distance); fit=cluster_sequences(subd,k,method,linkage,(int(seed)+b)%2_147_483_647,**kwargs); cur=fit.assignments.to_numpy(); cur_same=cur[:,None]==cur[None,:]
        ix=np.ix_(selected,selected); evaluated[ix]+=1; matched[ix]+=(cur_same==orig_same[ix]).astype(int)
        rows.append({"iteration":b,"n_sampled":len(selected),"average_silhouette":float(validate_sequence_clusters(fit)["overall"].iloc[0].average_silhouette)})
    stability=np.full((n,n),np.nan); valid=evaluated>0; stability[valid]=matched[valid]/evaluated[valid]; np.fill_diagonal(stability,1); pair=stability[np.triu_indices(n,1)]; finite=pair[np.isfinite(pair)]
    over=pd.DataFrame([{"n_boot":int(n_boot),"sample_fraction":float(sample_fraction),"mean_pairwise_stability":float(finite.mean()) if len(finite) else np.nan,"min_pairwise_stability":float(finite.min()) if len(finite) else np.nan}])
    return SequenceClusterBootstrap(original,pd.DataFrame(stability,index=ids,columns=ids),pd.DataFrame(evaluated,index=ids,columns=ids),pd.DataFrame(rows),over,{"k":int(k),"method":method,"linkage":linkage,"n_boot":int(n_boot),"sample_fraction":float(sample_fraction),"seed":int(seed)})


def summarise_sequence_cluster_stability(bootstrap:SequenceClusterBootstrap,threshold:float=.8)->dict[str,Any]:
    if not isinstance(bootstrap,SequenceClusterBootstrap): raise ValidationError("`bootstrap` must be created by `bootstrap_sequence_clusters()`.")
    scalar_number(threshold,"threshold",0,1); a=bootstrap.original.assignments; s=bootstrap.pairwise_stability; rows=[]
    for c in sorted(a.unique(),key=str):
        ids=a.index[a==c].tolist(); values=np.array([1.0]) if len(ids)==1 else s.loc[ids,ids].to_numpy()[np.triu_indices(len(ids),1)]; finite=values[np.isfinite(values)]; rows.append({"cluster":str(c),"n_sequences":len(ids),"mean_within_stability":float(finite.mean()) if len(finite) else np.nan,"min_within_stability":float(finite.min()) if len(finite) else np.nan,"n_evaluated_pairs":0 if len(ids)==1 else len(finite)})
    lows=[]; ids=s.index.tolist(); arr=s.to_numpy()
    for i in range(len(ids)-1):
        for j in range(i+1,len(ids)):
            if np.isfinite(arr[i,j]) and arr[i,j]<threshold: lows.append({"sequence_id_1":ids[i],"sequence_id_2":ids[j],"stability":float(arr[i,j])})
    return {"overall":bootstrap.overall,"clusters":pd.DataFrame(rows),"low_stability_pairs":pd.DataFrame(lows,columns=["sequence_id_1","sequence_id_2","stability"]),"threshold":threshold}


def create_sequence_cluster_ensemble(*solutions:Any,k:int,linkage:str="average")->SequenceClusterEnsemble:
    if len(solutions)<2: raise ValidationError("Supply at least two clustering solutions.")
    scalar_number(k,"k",lower=2,integer=True)
    allowed={"ward.D","ward.D2","single","complete","average","mcquitty","median","centroid"}
    if linkage not in allowed: raise ValidationError("`linkage` is not a supported `stats::hclust()` method.")
    ass=[]
    for sol in solutions:
        a=sol.assignments.copy() if isinstance(sol,(SequenceClustering,SequenceClusterEnsemble)) else sol.copy() if isinstance(sol,pd.Series) else None
        if a is None or a.isna().any() or a.index.has_duplicates: raise ValidationError("Every solution must provide non-missing assignments with unique sequence-ID names.")
        a.index=a.index.astype(str); ass.append(a)
    ids=ass[0].index.tolist()
    if any(set(a.index)!=set(ids) for a in ass): raise ValidationError("All clustering solutions must cover the same sequence IDs.")
    n=len(ids)
    if k>=n: raise ValidationError("`k` must be smaller than the number of sequences.")
    co=np.zeros((n,n),float)
    for a in ass:
        vals=a.reindex(ids).to_numpy(); co+=(vals[:,None]==vals[None,:])
    co/=len(ass); np.fill_diagonal(co,1); dm=1-co
    dist=_distance_result_from_matrix(dm,ids); consensus,model,_=_hierarchical(dm,ids,int(k),linkage)
    return SequenceClusterEnsemble(consensus,pd.DataFrame(co,index=ids,columns=ids),dist,model,[a.reindex(ids) for a in ass],int(k),linkage)
