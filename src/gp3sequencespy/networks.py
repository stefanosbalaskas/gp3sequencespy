from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

import numpy as np
import pandas as pd

from ._advanced import adv_data, group_key, match_cols, scalar_character, scalar_logical, scalar_number, vector_normalise
from ._exceptions import ValidationError


@dataclass(slots=True)
class HigherOrderTransitionModel:
    order: int
    tables: dict[str, pd.DataFrame]
    state_levels: list[str]
    smoothing: float
    backoff: bool
    context_separator: str


def create_transition_network(data:Any,sequence_id_col:str="sequence_id",order_col:str="sequence_order",state_col:str="state",group_cols:Sequence[str]|str|None=None,order:int=1,include_self:bool=True,normalise:str="count",smoothing:float=0,context_separator:str=" > ")->pd.DataFrame:
    if normalise not in {"count","from","global"}: raise ValidationError("Invalid normalise value.")
    scalar_number(order,"order",lower=1,integer=True); scalar_logical(include_self,"include_self"); scalar_number(smoothing,"smoothing",lower=0); scalar_character(context_separator,"context_separator")
    x=adv_data(data,sequence_id_col,order_col,state_col,group_cols,"error")
    if any(context_separator in s for s in x["state_levels"]): raise ValidationError("`context_separator` must not occur inside an observed state label.")
    groups=match_cols(x["data"],group_cols,"group_cols")
    if groups:
        meta=x["metadata"].copy(); meta=meta.rename(columns={sequence_id_col:"sequence_id"}); meta[".group_key"]=group_key(meta,groups)
    else: meta=pd.DataFrame({"sequence_id":x["sequence_ids"],".group_key":["__all__"]*len(x["sequence_ids"])})
    events=[]
    for sid in x["sequence_ids"]:
        seq=x["sequences"][sid]
        if len(seq)<=order: continue
        mr=meta.loc[meta.sequence_id.astype(str)==sid].iloc[0]
        for i in range(len(seq)-order):
            context=seq[i:i+order]; nxt=seq[i+order]
            if order==1 and not include_self and context[0]==nxt: continue
            rec={c:mr[c] for c in groups}; rec.update(group_key=mr[".group_key"],sequence_id=sid,context=context_separator.join(context),from_state=context[0] if order==1 else np.nan,to_state=nxt); events.append(rec)
    basecols=[*groups,"group_key","context","from_state","to_state","count","weight","sequence_count","sequence_prevalence"]
    if not events:
        out=pd.DataFrame(columns=basecols); out.attrs.update(gp3_class="gp3_transition_network",group_cols=groups,settings={"order":int(order),"normalise":normalise,"include_self":include_self,"smoothing":smoothing,"context_separator":context_separator}); return out
    ev=pd.DataFrame(events); grouping=[*groups,"group_key","context","from_state","to_state"]
    # dropna=False is critical because higher-order from_state is NA.
    rows=[]
    for key,part in ev.groupby(grouping,sort=True,dropna=False):
        vals=key if isinstance(key,tuple) else (key,); rec=dict(zip(grouping,vals,strict=True)); gk=str(rec["group_key"]); nseq=int((meta[".group_key"].astype(str)==gk).sum()); sc=part.sequence_id.nunique(); rec.update(count=float(len(part)+smoothing),sequence_count=int(sc),sequence_prevalence=float(sc/nseq)); rows.append(rec)
    out=pd.DataFrame(rows)
    if normalise=="count": out["weight"]=out["count"]
    elif normalise=="from": out["weight"]=out["count"]/out.groupby([*groups,"group_key","context"],dropna=False)["count"].transform("sum")
    else: out["weight"]=out["count"]/out.groupby([*groups,"group_key"],dropna=False)["count"].transform("sum")
    out=out.sort_values(["group_key","context","to_state"],kind="stable").reset_index(drop=True)[basecols]
    out.attrs.update(gp3_class="gp3_transition_network",group_cols=groups,settings={"order":int(order),"normalise":normalise,"include_self":include_self,"smoothing":smoothing,"context_separator":context_separator})
    return out


def _graph_matrix(network:pd.DataFrame,use_weight:bool=True,symmetrise:bool=False)->pd.DataFrame:
    if not isinstance(network,pd.DataFrame) or network.attrs.get("gp3_class")!="gp3_transition_network": raise ValidationError("`network` must be created by `create_transition_network()`.")
    if network.attrs.get("settings",{}).get("order")!=1: raise ValidationError("Centrality and community helpers currently require a first-order network.")
    gks=[str(x) for x in pd.unique(network.group_key.dropna())]
    if len(gks)>1: raise ValidationError("Filter a grouped transition network to one group before graph analysis.")
    states=sorted(set(network.from_state.dropna().astype(str)).union(network.to_state.dropna().astype(str)))
    a=pd.DataFrame(0.0,index=states,columns=states)
    vals=network.weight.to_numpy(float) if use_weight else np.ones(len(network))
    for (_,r),v in zip(network.iterrows(),vals,strict=True): a.loc[str(r.from_state),str(r.to_state)]+=v
    if symmetrise:
        diag=np.diag(a.to_numpy()).copy(); a=a+a.T; np.fill_diagonal(a.values,diag)
    return a


def _dijkstra(cost:np.ndarray,source:int)->np.ndarray:
    n=len(cost); distance=np.full(n,np.inf); visited=np.zeros(n,bool); distance[source]=0
    for _ in range(n):
        available=np.flatnonzero(~visited)
        if not len(available): break
        current=available[int(np.argmin(distance[available]))]
        if not np.isfinite(distance[current]): break
        visited[current]=True
        neighbours=np.flatnonzero(np.isfinite(cost[current]) & (cost[current]>0))
        for j in neighbours:
            cand=distance[current]+cost[current,j]
            if cand<distance[j]: distance[j]=cand
    return distance


def _betweenness(binary:np.ndarray)->np.ndarray:
    n=len(binary); score=np.zeros(n,float)
    for source in range(n):
        stack=[]; predecessors=[[] for _ in range(n)]; sigma=np.zeros(n); sigma[source]=1; dist=np.full(n,-1,int); dist[source]=0; queue=[source]
        while queue:
            v=queue.pop(0); stack.append(v)
            for w in np.flatnonzero(binary[v]):
                if dist[w]<0: queue.append(int(w)); dist[w]=dist[v]+1
                if dist[w]==dist[v]+1: sigma[w]+=sigma[v]; predecessors[w].append(v)
        dep=np.zeros(n)
        while stack:
            w=stack.pop()
            for v in predecessors[w]:
                if sigma[w]>0: dep[v]+=(sigma[v]/sigma[w])*(1+dep[w])
            if w!=source: score[w]+=dep[w]
    return score


def summarise_transition_centrality(network:pd.DataFrame,directed:bool=True,pagerank_damping:float=.85,pagerank_tolerance:float=1e-10,pagerank_max_iter:int=1000)->pd.DataFrame:
    scalar_logical(directed,"directed"); scalar_number(pagerank_damping,"pagerank_damping",0,1); scalar_number(pagerank_tolerance,"pagerank_tolerance",0); scalar_number(pagerank_max_iter,"pagerank_max_iter",1,integer=True)
    adf=_graph_matrix(network,True,not directed); a=adf.to_numpy(); n=len(a)
    if n==0:return pd.DataFrame()
    binary=a>0; out_degree=binary.sum(1); in_degree=binary.sum(0); out_strength=a.sum(1); in_strength=a.sum(0); total_degree=out_degree+in_degree if directed else out_degree; total_strength=out_strength+in_strength if directed else out_strength
    cost=np.full_like(a,np.inf); cost[a>0]=1/a[a>0]; np.fill_diagonal(cost,0); d=np.vstack([_dijkstra(cost,i) for i in range(n)]); closeness=[]
    for i in range(n):
        reach=d[i,np.isfinite(d[i])&(d[i]>0)]; closeness.append(0.0 if not len(reach) else float(len(reach)/reach.sum()))
    between=_betweenness(binary); between=between/2 if not directed else between
    transition=a.copy(); dangling=transition.sum(1)==0
    if (~dangling).any(): transition[~dangling]/=transition[~dangling].sum(1,keepdims=True)
    if dangling.any(): transition[dangling]=1/n
    rank=np.repeat(1/n,n)
    for _ in range(int(pagerank_max_iter)):
        nxt=(1-pagerank_damping)/n+pagerank_damping*(transition.T@rank)
        if np.max(np.abs(nxt-rank))<pagerank_tolerance: rank=nxt; break
        rank=nxt
    rank=vector_normalise(rank)
    return pd.DataFrame({"state":adf.index,"out_degree":out_degree.astype(int),"in_degree":in_degree.astype(int),"total_degree":total_degree.astype(int),"out_strength":out_strength,"in_strength":in_strength,"total_strength":total_strength,"closeness":closeness,"betweenness":between,"pagerank":rank})


def detect_transition_communities(network:pd.DataFrame,method:str="label_propagation",max_iter:int=100,seed:int=1)->pd.DataFrame:
    if method not in {"label_propagation","components"}: raise ValidationError("Invalid community method.")
    scalar_number(max_iter,"max_iter",1,integer=True); scalar_number(seed,"seed",0,integer=True); adf=_graph_matrix(network,True,True); a=adf.to_numpy(); n=len(a)
    if n==0:return pd.DataFrame(columns=["state","community"])
    labels=np.arange(1,n+1,dtype=int)
    if method=="components":
        community=np.full(n,-1,int); current=0
        for i in range(n):
            if community[i]>=0: continue
            current+=1; queue=[i]; community[i]=current
            while queue:
                v=queue.pop(0); neigh=np.flatnonzero(a[v]>0); unseen=[int(q) for q in neigh if community[q]<0]
                for q in unseen: community[q]=current
                queue.extend(unseen)
        labels=community
    else:
        order=np.arange(n); shift=int(seed%n) if n>1 else 0
        if shift: order=np.r_[order[shift:],order[:shift]]
        for _ in range(int(max_iter)):
            changed=False
            for v in order:
                neigh=np.flatnonzero(a[v]>0)
                if not len(neigh): continue
                totals={}
                for w in neigh: totals[int(labels[w])]=totals.get(int(labels[w]),0)+float(a[v,w])
                mx=max(totals.values()); new=min(k for k,val in totals.items() if val==mx)
                if new!=labels[v]: labels[v]=new; changed=True
            if not changed: break
        unique=sorted(set(labels.tolist())); remap={v:i+1 for i,v in enumerate(unique)}; labels=np.array([remap[x] for x in labels])
    return pd.DataFrame({"state":adf.index,"community":labels.astype(int)})


def fit_higher_order_transition_model(data:Any,sequence_id_col:str="sequence_id",order_col:str="sequence_order",state_col:str="state",order:int=2,smoothing:float=.5,backoff:bool=True,context_separator:str=" > ")->HigherOrderTransitionModel:
    scalar_number(order,"order",1,integer=True); scalar_number(smoothing,"smoothing",0); scalar_logical(backoff,"backoff"); scalar_character(context_separator,"context_separator"); x=adv_data(data,sequence_id_col,order_col,state_col,missing_state_policy="error")
    if any(context_separator in s for s in x["state_levels"]): raise ValidationError("`context_separator` must not occur inside an observed state label.")
    def build(level:int)->pd.DataFrame:
        ev=[]
        for sid in x["sequence_ids"]:
            seq=x["sequences"][sid]
            for i in range(max(0,len(seq)-level)): ev.append((context_separator.join(seq[i:i+level]),seq[i+level]))
        rows=[]
        for context in sorted(set(c for c,_ in ev)):
            counts={s:0 for s in x["state_levels"]}
            for c,s in ev:
                if c==context: counts[s]+=1
            den=sum(counts.values())+smoothing*len(counts)
            probs={s:(counts[s]+smoothing)/den for s in x["state_levels"]}
            for s in x["state_levels"]: rows.append({"order":level,"context":context,"next_state":s,"count":int(counts[s]),"probability":float(probs[s])})
        return pd.DataFrame(rows,columns=["order","context","next_state","count","probability"])
    levels=list(range(1,int(order)+1)) if backoff else [int(order)]; tables={f"order_{lev}":build(lev) for lev in levels}; return HigherOrderTransitionModel(int(order),tables,x["state_levels"],float(smoothing),bool(backoff),context_separator)


def predict_next_state(model:HigherOrderTransitionModel,history:Sequence[str]|str,top_n:int|None=None)->pd.DataFrame:
    if not isinstance(model,HigherOrderTransitionModel): raise ValidationError("`model` must be created by `fit_higher_order_transition_model()`.")
    history=[history] if isinstance(history,str) else list(history)
    if not history or any(not isinstance(x,str) or not x.strip() for x in history): raise ValidationError("`history` must be a non-missing, non-blank character vector.")
    if top_n is not None: scalar_number(top_n,"top_n",1,integer=True)
    used=0; context_used="<unseen>"; table_used=None
    for level in sorted((int(k.split('_')[1]) for k in model.tables),reverse=True):
        if len(history)<level: continue
        context=model.context_separator.join(history[-level:]); tab=model.tables[f"order_{level}"]; cur=tab.loc[tab.context==context].copy()
        if len(cur): used=level; context_used=context; table_used=cur; break
    if table_used is None:
        table_used=pd.DataFrame({"order":[0]*len(model.state_levels),"context":["<unseen>"]*len(model.state_levels),"next_state":model.state_levels,"count":[0]*len(model.state_levels),"probability":[1/len(model.state_levels)]*len(model.state_levels)})
    table_used=table_used.sort_values(["probability","next_state"],ascending=[False,True],kind="stable")
    if top_n is not None: table_used=table_used.head(int(top_n))
    table_used=table_used.copy(); table_used["used_order"]=used; table_used["used_context"]=context_used; return table_used.reset_index(drop=True)


def bootstrap_transition_network(data:Any,sequence_id_col:str="sequence_id",order_col:str="sequence_order",state_col:str="state",n_boot:int=100,level:float=.95,seed:int=1,include_self:bool=True)->pd.DataFrame:
    scalar_number(n_boot,"n_boot",1,integer=True); scalar_number(level,"level",.5,.999); scalar_number(seed,"seed",0,integer=True); scalar_logical(include_self,"include_self"); x=adv_data(data,sequence_id_col,order_col,state_col,missing_state_policy="error")
    observed=create_transition_network(x["data"],sequence_id_col,order_col,state_col,include_self=include_self,normalise="from")
    if len(observed)==0: raise ValidationError("No first-order transitions are available to bootstrap.")
    keys=[f"{a}\x1c{b}" for a,b in zip(observed.from_state,observed.to_state,strict=True)]; vals=np.zeros((len(keys),int(n_boot))); rng=np.random.default_rng(seed)
    for b in range(int(n_boot)):
        sampled=rng.choice(x["sequence_ids"],len(x["sequence_ids"]),replace=True); pieces=[]
        for i,sid in enumerate(sampled,1):
            cur=x["data"].loc[x["data"][sequence_id_col].astype(str)==sid].copy(); cur[sequence_id_col]=f"boot{b+1}_{i}"; pieces.append(cur)
        boot=create_transition_network(pd.concat(pieces,ignore_index=True),sequence_id_col,order_col,state_col,include_self=include_self,normalise="from"); bm={f"{a}\x1c{bb}":float(w) for a,bb,w in zip(boot.from_state,boot.to_state,boot.weight,strict=True)}; vals[:,b]=[bm.get(k,0) for k in keys]
    alpha=(1-level)/2; out=observed.copy(); out["bootstrap_mean"]=vals.mean(1); out["bootstrap_sd"]=vals.std(1,ddof=1) if n_boot>1 else np.nan; out["conf_low"]=np.quantile(vals,alpha,axis=1); out["conf_high"]=np.quantile(vals,1-alpha,axis=1); out["n_boot"]=int(n_boot); out["confidence_level"]=float(level); return out
