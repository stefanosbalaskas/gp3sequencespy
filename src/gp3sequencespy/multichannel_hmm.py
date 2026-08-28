from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence
import numpy as np
import pandas as pd

from ._advanced import adv_data, row_normalise, scalar_character, scalar_logical, scalar_number, vector_normalise
from ._exceptions import ValidationError

@dataclass(slots=True)
class MultichannelSequenceHMM:
    initial_probs:np.ndarray; transition_probs:np.ndarray; emission_probs:dict[str,np.ndarray]
    state_names:list[str]; channel_names:list[str]; symbol_names:dict[str,list[str]]; sequence_ids:list[str]
    sequence_log_likelihoods:pd.Series; log_likelihood:float; iterations:int; converged:bool; tolerance:float; pseudocount:float; log_likelihood_history:np.ndarray
    n_parameters:int; n_observations:int; aic:float; bic:float; seed:int; training_observations:dict[str,np.ndarray]; training_orders:dict[str,list[Any]]; posteriors:list[dict[str,Any]]|None; columns:dict[str,str]


def _input(data:Any,sequence_id_col:str,order_col:str,channel_cols:Sequence[str],symbol_levels:Sequence[Sequence[str]|None]|dict[str,Sequence[str]]|None=None):
    channels=list(channel_cols)
    if len(channels)<2 or len(set(channels))!=len(channels) or any(not isinstance(c,str) or not c for c in channels):raise ValidationError("`channel_cols` must contain at least two unique channel names.")
    if not isinstance(data,pd.DataFrame) and hasattr(data,"data"):data=data.data
    if not isinstance(data,pd.DataFrame):raise ValidationError("`data` must be a data frame.")
    missing=[c for c in channels if c not in data.columns]
    if missing:raise ValidationError("Missing channel columns: "+", ".join(missing)+".")
    x=adv_data(data,sequence_id_col,order_col,channels[0],missing_state_policy="error");w=x["data"]
    for c in channels:
        text=w[c].astype("string")
        if w[c].isna().any() or text.str.strip().eq("").any():raise ValidationError(f"Channel `{c}` contains missing, blank, or non-atomic values.")
    if symbol_levels is None: sl={c:None for c in channels}
    elif isinstance(symbol_levels,dict):sl={c:symbol_levels.get(c) for c in channels}
    else:
        if len(symbol_levels)!=len(channels):raise ValidationError("`symbol_levels` must be `NULL` or one list element per channel.")
        sl=dict(zip(channels,symbol_levels,strict=True))
    symbols={}
    for c in channels:
        observed=list(dict.fromkeys(w[c].astype(str).tolist())); cur=sl[c]
        if cur is None:
            cur=[str(z) for z in w[c].cat.categories if str(z) in observed] if isinstance(w[c].dtype,pd.CategoricalDtype) else sorted(observed)
        cur=[str(z) for z in cur]
        if not cur or len(set(cur))!=len(cur) or any(not z.strip() for z in cur):raise ValidationError(f"Invalid symbol levels for channel `{c}`.")
        miss=[z for z in observed if z not in cur]
        if miss:raise ValidationError(f"Symbol levels for channel `{c}` do not cover: "+", ".join(miss)+".")
        symbols[c]=cur
    observations={};orders={}
    for sid in x["sequence_ids"]:
        part=w.loc[w[sequence_id_col].astype(str)==sid];mat=np.zeros((len(part),len(channels)),int)
        for j,c in enumerate(channels):idx={s:i for i,s in enumerate(symbols[c])};mat[:,j]=[idx[z] for z in part[c].astype(str)]
        observations[sid]=mat;orders[sid]=part[order_col].tolist()
    return {"data":w,"sequence_ids":x["sequence_ids"],"observations":observations,"orders":orders,"channel_cols":channels,"symbols":symbols,"columns":{"sequence_id":sequence_id_col,"order":order_col}}


def _likelihood(obs:np.ndarray,emissions:dict[str,np.ndarray],channels:list[str])->np.ndarray:
    k=next(iter(emissions.values())).shape[0];like=np.ones((len(obs),k))
    for j,c in enumerate(channels):like*=emissions[c][:,obs[:,j]].T
    return like


def _fb(like:np.ndarray,initial:np.ndarray,transition:np.ndarray):
    n,k=like.shape;alpha=np.zeros((n,k));sc=np.zeros(n);alpha[0]=initial*like[0];sc[0]=max(alpha[0].sum(),np.finfo(float).tiny);alpha[0]/=sc[0]
    for t in range(1,n):alpha[t]=(alpha[t-1]@transition)*like[t];sc[t]=max(alpha[t].sum(),np.finfo(float).tiny);alpha[t]/=sc[t]
    beta=np.ones((n,k))
    for t in range(n-2,-1,-1):beta[t]=transition@(like[t+1]*beta[t+1]);beta[t]/=sc[t+1]
    gamma=alpha*beta;gamma/=gamma.sum(1,keepdims=True);xi=np.zeros((max(0,n-1),k,k))
    for t in range(n-1):cur=np.outer(alpha[t],like[t+1]*beta[t+1])*transition;xi[t]=cur/cur.sum() if cur.sum()>0 else cur
    return {"gamma":gamma,"xi":xi,"log_likelihood":float(np.log(sc).sum())}


def _vit(like,initial,transition):
    n,k=like.shape;li=np.log(np.maximum(initial,np.finfo(float).tiny));lt=np.log(np.maximum(transition,np.finfo(float).tiny));ll=np.log(np.maximum(like,np.finfo(float).tiny));delta=np.full((n,k),-np.inf);psi=np.zeros((n,k),int);delta[0]=li+ll[0]
    for t in range(1,n):
        for j in range(k):cand=delta[t-1]+lt[:,j];psi[t,j]=np.argmax(cand);delta[t,j]=cand[psi[t,j]]+ll[t,j]
    path=np.zeros(n,int);path[-1]=np.argmax(delta[-1])
    for t in range(n-2,-1,-1):path[t]=psi[t+1,path[t+1]]
    return path


def fit_multichannel_sequence_hmm(data:Any,n_states:int,channel_cols:Sequence[str],sequence_id_col:str="sequence_id",order_col:str="sequence_order",symbol_levels=None,state_names:Sequence[str]|None=None,initial_probs=None,transition_probs=None,emission_probs=None,max_iter:int=200,tolerance:float=1e-6,pseudocount:float=1e-6,seed:int=1,keep_posteriors:bool=False)->MultichannelSequenceHMM:
    scalar_number(n_states,"n_states",1,integer=True);scalar_number(max_iter,"max_iter",1,integer=True);scalar_number(tolerance,"tolerance",0);scalar_number(pseudocount,"pseudocount",0);scalar_number(seed,"seed",0,integer=True);scalar_logical(keep_posteriors,"keep_posteriors");inp=_input(data,sequence_id_col,order_col,channel_cols,symbol_levels);channels=inp["channel_cols"]
    states=[f"latent_{i+1}" for i in range(n_states)] if state_names is None else [str(x) for x in state_names]
    if len(states)!=n_states or len(set(states))!=len(states) or any(not x.strip() for x in states):raise ValidationError("`state_names` must uniquely name all latent states.")
    rng=np.random.default_rng(seed);initial=np.asarray(initial_probs,float) if initial_probs is not None else rng.exponential(size=n_states)+.1;trans=np.asarray(transition_probs,float) if transition_probs is not None else rng.exponential(size=(n_states,n_states))+.1
    if initial.shape!=(n_states,) or not np.isfinite(initial).all() or (initial<0).any():raise ValidationError("Invalid `initial_probs`.")
    if trans.shape!=(n_states,n_states) or not np.isfinite(trans).all() or (trans<0).any():raise ValidationError("Invalid `transition_probs`.")
    if emission_probs is None:ems={c:rng.exponential(size=(n_states,len(inp["symbols"][c])))+.1 for c in channels}
    elif isinstance(emission_probs,dict):ems={c:np.asarray(emission_probs[c],float) for c in channels}
    else:
        if len(emission_probs)!=len(channels):raise ValidationError("`emission_probs` must contain one matrix per channel.")
        ems={c:np.asarray(v,float) for c,v in zip(channels,emission_probs,strict=True)}
    for c in channels:
        if ems[c].shape!=(n_states,len(inp["symbols"][c])) or not np.isfinite(ems[c]).all() or (ems[c]<0).any():raise ValidationError(f"Invalid emission probabilities for channel `{c}`.")
        ems[c]=row_normalise(ems[c])
    initial=vector_normalise(initial);trans=row_normalise(trans);history=[];previous=-np.inf;converged=False
    obslist=[inp["observations"][sid] for sid in inp["sequence_ids"]]
    for it in range(1,max_iter+1):
        ic=np.full(n_states,pseudocount);tc=np.full((n_states,n_states),pseudocount);ec={c:np.full((n_states,len(inp["symbols"][c])),pseudocount) for c in channels};ll=[]
        for obs in obslist:
            fb=_fb(_likelihood(obs,ems,channels),initial,trans);ic+=fb["gamma"][0];
            if len(obs)>1:tc+=fb["xi"].sum(0)
            for j,c in enumerate(channels):
                for t,sym in enumerate(obs[:,j]):ec[c][:,sym]+=fb["gamma"][t]
            ll.append(fb["log_likelihood"])
        current=float(np.sum(ll));history.append(current);initial=vector_normalise(ic);trans=row_normalise(tc);ems={c:row_normalise(ec[c]) for c in channels}
        if it>1 and abs(current-previous)/max(1,abs(previous))<=tolerance:converged=True;break
        previous=current
    final=[];posts=[]
    for obs in obslist:fb=_fb(_likelihood(obs,ems,channels),initial,trans);final.append(fb["log_likelihood"]);posts.append(fb)
    ll=float(np.sum(final));history[-1]=ll;npar=(n_states-1)+n_states*(n_states-1)+sum(n_states*(len(inp["symbols"][c])-1) for c in channels);nobs=sum(len(o) for o in obslist);return MultichannelSequenceHMM(initial,trans,ems,states,channels,inp["symbols"],inp["sequence_ids"],pd.Series(final,index=inp["sequence_ids"]),ll,len(history),converged,float(tolerance),float(pseudocount),np.array(history),int(npar),int(nobs),float(-2*ll+2*npar),float(-2*ll+np.log(max(1,nobs))*npar),int(seed),inp["observations"],inp["orders"],posts if keep_posteriors else None,inp["columns"])


def decode_multichannel_sequence_states(model:MultichannelSequenceHMM,data:Any=None,sequence_id_col:str="sequence_id",order_col:str="sequence_order",channel_cols:Sequence[str]|None=None,method:str="viterbi")->pd.DataFrame:
    if not isinstance(model,MultichannelSequenceHMM):raise ValidationError("`model` must be created by `fit_multichannel_sequence_hmm()`.")
    if method not in {"viterbi","posterior"}:raise ValidationError("Invalid method.")
    channels=model.channel_names if channel_cols is None else list(channel_cols)
    if data is None:obs=model.training_observations;orders=model.training_orders;ids=model.sequence_ids
    else:inp=_input(data,sequence_id_col,order_col,channels,model.symbol_names);obs=inp["observations"];orders=inp["orders"];ids=inp["sequence_ids"]
    rows=[]
    for sid in ids:
        o=obs[sid];like=_likelihood(o,model.emission_probs,model.channel_names);fb=_fb(like,model.initial_probs,model.transition_probs);dec=_vit(like,model.initial_probs,model.transition_probs) if method=="viterbi" else np.argmax(fb["gamma"],axis=1);prob=fb["gamma"][np.arange(len(dec)),dec]
        for t,k in enumerate(dec):
            rec={"sequence_id":sid,"sequence_order":orders[sid][t],"latent_state":model.state_names[k],"posterior_probability":float(prob[t]),"decoding_method":method}
            for j,c in enumerate(model.channel_names):rec[c]=model.symbol_names[c][o[t,j]]
            rows.append(rec)
    return pd.DataFrame(rows)


def summarise_multichannel_sequence_hmm(model:MultichannelSequenceHMM)->dict[str,Any]:
    if not isinstance(model,MultichannelSequenceHMM):raise ValidationError("`model` must be created by `fit_multichannel_sequence_hmm()`.")
    fit=pd.DataFrame([{"n_states":len(model.state_names),"n_channels":len(model.channel_names),"n_sequences":len(model.sequence_ids),"n_observations":model.n_observations,"log_likelihood":model.log_likelihood,"aic":model.aic,"bic":model.bic,"iterations":model.iterations,"converged":model.converged}]);initial=pd.DataFrame({"latent_state":model.state_names,"probability":model.initial_probs});transition=pd.DataFrame([{"from_state":a,"to_state":b,"probability":float(model.transition_probs[i,j])} for i,a in enumerate(model.state_names) for j,b in enumerate(model.state_names)]);emission={c:pd.DataFrame([{"latent_state":a,"observed_state":b,"probability":float(model.emission_probs[c][i,j])} for i,a in enumerate(model.state_names) for j,b in enumerate(model.symbol_names[c])]) for c in model.channel_names};return {"fit":fit,"initial":initial,"transition":transition,"emission":emission}


def plot_multichannel_sequence_hmm(model:MultichannelSequenceHMM,channel:str|None=None,ax=None,**kwargs):
    import matplotlib.pyplot as plt
    if not isinstance(model,MultichannelSequenceHMM):raise ValidationError("`model` must be created by `fit_multichannel_sequence_hmm()`.")
    channel=model.channel_names[0] if channel is None else channel;scalar_character(channel,"channel")
    if channel not in model.channel_names:raise ValidationError("Unknown channel.")
    m=model.emission_probs[channel];ax=ax or plt.gca();x=np.arange(len(model.state_names));width=.8/max(1,len(model.symbol_names[channel]))
    for j,s in enumerate(model.symbol_names[channel]):ax.bar(x+j*width,m[:,j],width,label=s,**kwargs)
    ax.set_xticks(x+width*(len(model.symbol_names[channel])-1)/2,model.state_names);ax.set_ylabel("Emission probability");ax.legend();return m
