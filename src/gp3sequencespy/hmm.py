from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence
import numpy as np
import pandas as pd

from ._advanced import adv_data, forward_backward, row_normalise, scalar_logical, scalar_number, vector_normalise, viterbi
from ._exceptions import ModelFitError, ValidationError

@dataclass(slots=True)
class SequenceHMM:
    initial_probs: np.ndarray
    transition_probs: np.ndarray
    emission_probs: np.ndarray
    state_names: list[str]
    symbol_names: list[str]
    sequence_ids: list[str]
    log_likelihood: float
    sequence_log_likelihoods: pd.Series
    iterations: int
    converged: bool
    tolerance: float
    pseudocount: float
    log_likelihood_history: np.ndarray
    n_parameters: int
    n_observations: int
    aic: float
    bic: float
    seed: int
    posteriors: list[dict[str,Any]]|None
    training_sequences: dict[str,list[str]]
    training_orders: dict[str,list[Any]]

@dataclass(slots=True)
class HMMComponent:
    initial_probs: np.ndarray
    transition_probs: np.ndarray
    emission_probs: np.ndarray
    state_names: list[str]
    symbol_names: list[str]

@dataclass(slots=True)
class SequenceHMMMixture:
    mixture_weights: np.ndarray
    components: list[HMMComponent]
    responsibilities: pd.DataFrame
    log_likelihood: float
    log_likelihood_history: np.ndarray
    iterations: int
    converged: bool
    tolerance: float
    pseudocount: float
    inner_initial_iter: int
    n_components: int
    n_states: list[int]
    n_parameters: int
    n_observations: int
    aic: float
    bic: float
    symbol_names: list[str]
    sequence_ids: list[str]
    seed: int
    training_sequences: dict[str,list[str]]
    training_orders: dict[str,list[Any]]


def _hmm_input(data:Any,sequence_id_col:str,order_col:str,state_col:str,symbol_levels:Sequence[str]|None=None):
    x=adv_data(data,sequence_id_col,order_col,state_col,missing_state_policy="error"); symbols=x["state_levels"] if symbol_levels is None else [str(s) for s in symbol_levels]
    if not symbols or len(set(symbols))!=len(symbols) or any(not s.strip() for s in symbols):raise ValidationError("`symbol_levels` must contain unique, non-missing, non-blank symbols.")
    missing=[s for s in x["state_levels"] if s not in symbols]
    if missing:raise ValidationError("`symbol_levels` does not cover observed symbols: "+", ".join(missing)+".")
    idx={s:i for i,s in enumerate(symbols)}; encoded={sid:np.array([idx[z] for z in x["sequences"][sid]],dtype=int) for sid in x["sequence_ids"]}; return x,symbols,encoded


def _init(n_states:int,n_symbols:int,seed:int,initial_probs=None,transition_probs=None,emission_probs=None):
    rng=np.random.default_rng(seed)
    initial=rng.exponential(size=n_states)+.1 if initial_probs is None else np.asarray(initial_probs,float)
    transition=rng.exponential(size=(n_states,n_states))+.1 if transition_probs is None else np.asarray(transition_probs,float)
    emission=rng.exponential(size=(n_states,n_symbols))+.1 if emission_probs is None else np.asarray(emission_probs,float)
    if initial.shape!=(n_states,) or not np.isfinite(initial).all() or (initial<0).any():raise ValidationError("Invalid `initial_probs`.")
    if transition.shape!=(n_states,n_states) or not np.isfinite(transition).all() or (transition<0).any():raise ValidationError("Invalid `transition_probs`.")
    if emission.shape!=(n_states,n_symbols) or not np.isfinite(emission).all() or (emission<0).any():raise ValidationError("Invalid `emission_probs`.")
    return {"initial":vector_normalise(initial),"transition":row_normalise(transition),"emission":row_normalise(emission)}


def _sufficient(encoded:list[np.ndarray],p:dict[str,np.ndarray],weights:np.ndarray|None=None,pseudocount:float=0):
    k=len(p["initial"]); ns=p["emission"].shape[1]; weights=np.ones(len(encoded)) if weights is None else np.asarray(weights,float)
    if len(weights)!=len(encoded) or not np.isfinite(weights).all() or (weights<0).any():raise ValidationError("`weights` must contain one finite non-negative value per sequence.")
    init=np.full(k,pseudocount,float); trans=np.full((k,k),pseudocount,float); emit=np.full((k,ns),pseudocount,float); lls=[]; posts=[]
    for obs,w in zip(encoded,weights,strict=True):
        fb=forward_backward(obs,p["initial"],p["transition"],p["emission"]); init+=w*fb["gamma"][0]
        if len(obs)>1:trans+=w*fb["xi"].sum(0)
        for t,sym in enumerate(obs):emit[:,sym]+=w*fb["gamma"][t]
        lls.append(fb["log_likelihood"]); posts.append(fb)
    return {"initial":init,"transition":trans,"emission":emit,"log_likelihoods":np.array(lls),"posterior":posts}


def fit_sequence_hmm(data:Any,n_states:int,sequence_id_col:str="sequence_id",order_col:str="sequence_order",state_col:str="state",symbol_levels:Sequence[str]|None=None,state_names:Sequence[str]|None=None,initial_probs=None,transition_probs=None,emission_probs=None,max_iter:int=200,tolerance:float=1e-6,pseudocount:float=1e-6,seed:int=1,keep_posteriors:bool=False)->SequenceHMM:
    scalar_number(n_states,"n_states",1,integer=True); scalar_number(max_iter,"max_iter",1,integer=True); scalar_number(tolerance,"tolerance",0); scalar_number(pseudocount,"pseudocount",0); scalar_number(seed,"seed",0,integer=True); scalar_logical(keep_posteriors,"keep_posteriors")
    x,symbols,encoded_map=_hmm_input(data,sequence_id_col,order_col,state_col,symbol_levels); encoded=[encoded_map[sid] for sid in x["sequence_ids"]]; state_names=[f"latent_{i+1}" for i in range(int(n_states))] if state_names is None else [str(s) for s in state_names]
    if len(state_names)!=n_states or len(set(state_names))!=len(state_names) or any(not s.strip() for s in state_names):raise ValidationError("`state_names` must uniquely name all latent states.")
    p=_init(int(n_states),len(symbols),int(seed),initial_probs,transition_probs,emission_probs); history=[]; previous=-np.inf; converged=False
    for iteration in range(1,int(max_iter)+1):
        suf=_sufficient(encoded,p,pseudocount=pseudocount); current=float(suf["log_likelihoods"].sum()); history.append(current); p["initial"]=vector_normalise(suf["initial"]); p["transition"]=row_normalise(suf["transition"]); p["emission"]=row_normalise(suf["emission"])
        if iteration>1 and abs(current-previous)/max(1,abs(previous))<=tolerance:converged=True;break
        previous=current
    final=_sufficient(encoded,p,pseudocount=0); ll=float(final["log_likelihoods"].sum()); history[-1]=ll; npar=(n_states-1)+n_states*(n_states-1)+n_states*(len(symbols)-1); nobs=sum(map(len,encoded)); aic=-2*ll+2*npar; bic=-2*ll+np.log(max(1,nobs))*npar
    return SequenceHMM(p["initial"],p["transition"],p["emission"],state_names,symbols,x["sequence_ids"],ll,pd.Series(final["log_likelihoods"],index=x["sequence_ids"]),len(history),converged,float(tolerance),float(pseudocount),np.array(history),int(npar),int(nobs),float(aic),float(bic),int(seed),final["posterior"] if keep_posteriors else None,x["sequences"],x["orders"])


def _loglik(encoded:list[np.ndarray],p:dict[str,np.ndarray])->np.ndarray:return np.array([forward_backward(o,p["initial"],p["transition"],p["emission"])["log_likelihood"] for o in encoded])


def fit_sequence_hmm_mixture(data:Any,n_components:int,n_states:int|Sequence[int],sequence_id_col:str="sequence_id",order_col:str="sequence_order",state_col:str="state",symbol_levels:Sequence[str]|None=None,max_iter:int=200,inner_initial_iter:int=20,tolerance:float=1e-6,pseudocount:float=1e-6,seed:int=1)->SequenceHMMMixture:
    scalar_number(n_components,"n_components",2,integer=True); states=[int(n_states)]*int(n_components) if np.isscalar(n_states) else [int(x) for x in n_states]
    if len(states)!=n_components or any(x<1 for x in states):raise ValidationError("`n_states` must be a positive integer scalar or one value per component.")
    scalar_number(max_iter,"max_iter",1,integer=True); scalar_number(inner_initial_iter,"inner_initial_iter",1,integer=True); scalar_number(tolerance,"tolerance",0); scalar_number(pseudocount,"pseudocount",0); scalar_number(seed,"seed",0,integer=True)
    x,symbols,emap=_hmm_input(data,sequence_id_col,order_col,state_col,symbol_levels); encoded=[emap[sid] for sid in x["sequence_ids"]]; nseq=len(encoded)
    if n_components>nseq:raise ValidationError("More components than sequences were requested.")
    rng=np.random.default_rng(seed); raw=rng.exponential(size=(nseq,n_components))+.1; resp=raw/raw.sum(1,keepdims=True); params=[]
    for c,k in enumerate(states):
        p=_init(k,len(symbols),(int(seed)+c+1)%2_147_483_647)
        for _ in range(int(inner_initial_iter)):
            suf=_sufficient(encoded,p,resp[:,c],pseudocount); p["initial"]=vector_normalise(suf["initial"]); p["transition"]=row_normalise(suf["transition"]); p["emission"]=row_normalise(suf["emission"])
        params.append(p)
    mix=vector_normalise(resp.mean(0)); history=[]; previous=-np.inf; converged=False
    for iteration in range(1,int(max_iter)+1):
        cll=np.column_stack([_loglik(encoded,p) for p in params]); joint=cll+np.log(np.maximum(mix,np.finfo(float).tiny)); rowmax=joint.max(1); stab=np.exp(joint-rowmax[:,None]); total=stab.sum(1)
        if (~np.isfinite(total)|(total<=0)).any():raise ModelFitError("Mixture responsibilities could not be normalised.")
        resp=stab/total[:,None]; current=float((rowmax+np.log(total)).sum()); history.append(current); mix=vector_normalise(resp.mean(0),pseudocount)
        for c,p in enumerate(params):
            suf=_sufficient(encoded,p,resp[:,c],pseudocount); p["initial"]=vector_normalise(suf["initial"]);p["transition"]=row_normalise(suf["transition"]);p["emission"]=row_normalise(suf["emission"])
        if iteration>1 and abs(current-previous)/max(1,abs(previous))<=tolerance:converged=True;break
        previous=current
    cll=np.column_stack([_loglik(encoded,p) for p in params]); joint=cll+np.log(np.maximum(mix,np.finfo(float).tiny)); rowmax=joint.max(1); stab=np.exp(joint-rowmax[:,None]); total=stab.sum(1); resp=stab/total[:,None]; ll=float((rowmax+np.log(total)).sum()); history[-1]=ll
    comps=[]
    for c,(k,p) in enumerate(zip(states,params,strict=True),1):comps.append(HMMComponent(p["initial"],p["transition"],p["emission"],[f"component_{c}_latent_{j+1}" for j in range(k)],symbols))
    hard=np.argmax(resp,axis=1)+1; rdf=pd.DataFrame({"sequence_id":x["sequence_ids"],**{f"component_{c+1}":resp[:,c] for c in range(n_components)},"assigned_component":hard})
    npar=(n_components-1)+sum((k-1)+k*(k-1)+k*(len(symbols)-1) for k in states); nobs=sum(map(len,encoded)); return SequenceHMMMixture(mix,comps,rdf,ll,np.array(history),len(history),converged,float(tolerance),float(pseudocount),int(inner_initial_iter),int(n_components),states,int(npar),int(nobs),float(-2*ll+2*npar),float(-2*ll+np.log(max(1,nobs))*npar),symbols,x["sequence_ids"],int(seed),x["sequences"],x["orders"])


def _parameters(model:SequenceHMM|HMMComponent)->dict[str,np.ndarray]:return {"initial":model.initial_probs,"transition":model.transition_probs,"emission":model.emission_probs}


def decode_sequence_states(model:SequenceHMM|SequenceHMMMixture,data:Any=None,sequence_id_col:str="sequence_id",order_col:str="sequence_order",state_col:str="state",method:str="viterbi",component:int|None=None)->pd.DataFrame:
    if method not in {"viterbi","posterior"}:raise ValidationError("Invalid decoding method.")
    if not isinstance(model,(SequenceHMM,SequenceHMMMixture)):raise ValidationError("Unsupported HMM model object.")
    symbols=model.symbol_names
    if data is None:seqs=model.training_sequences; orders=model.training_orders; ids=list(seqs)
    else:x,_,_= _hmm_input(data,sequence_id_col,order_col,state_col,symbols); seqs=x["sequences"];orders=x["orders"];ids=x["sequence_ids"]
    idx={s:i for i,s in enumerate(symbols)}; enc=[np.array([idx[z] for z in seqs[sid]],int) for sid in ids]
    if isinstance(model,SequenceHMMMixture):
        if component is not None:scalar_number(component,"component",1,model.n_components,integer=True); comps=np.repeat(int(component),len(ids))
        elif data is None:comps=model.responsibilities.set_index("sequence_id").loc[ids,"assigned_component"].to_numpy(int)
        else:
            ll=np.column_stack([_loglik(enc,_parameters(c))+np.log(max(model.mixture_weights[j],np.finfo(float).tiny)) for j,c in enumerate(model.components)]);comps=np.argmax(ll,axis=1)+1
    else:comps=np.ones(len(ids),int)
    rows=[]
    for i,sid in enumerate(ids):
        cur=model if isinstance(model,SequenceHMM) else model.components[comps[i]-1]; p=_parameters(cur); fb=forward_backward(enc[i],p["initial"],p["transition"],p["emission"])
        if method=="viterbi":dec=viterbi(enc[i],p["initial"],p["transition"],p["emission"])["path"]; probs=fb["gamma"][np.arange(len(dec)),dec]
        else:dec=np.argmax(fb["gamma"],axis=1);probs=fb["gamma"].max(1)
        for t,j in enumerate(dec):rows.append({"sequence_id":sid,"sequence_order":orders[sid][t],"observed_state":seqs[sid][t],"component":int(comps[i]),"latent_state":cur.state_names[int(j)],"posterior_probability":float(probs[t]),"decoding_method":method})
    return pd.DataFrame(rows)


def summarise_sequence_hmm(model:SequenceHMM|SequenceHMMMixture)->dict[str,Any]:
    if isinstance(model,SequenceHMM):
        initial=pd.DataFrame({"latent_state":model.state_names,"probability":model.initial_probs}); transition=pd.DataFrame([{"from_state":a,"to_state":b,"probability":float(model.transition_probs[i,j])} for i,a in enumerate(model.state_names) for j,b in enumerate(model.state_names)]); emission=pd.DataFrame([{"latent_state":a,"observed_state":b,"probability":float(model.emission_probs[i,j])} for i,a in enumerate(model.state_names) for j,b in enumerate(model.symbol_names)]); fit=pd.DataFrame([{"log_likelihood":model.log_likelihood,"aic":model.aic,"bic":model.bic,"n_parameters":model.n_parameters,"n_observations":model.n_observations,"iterations":model.iterations,"converged":model.converged}]);return {"fit":fit,"initial":initial,"transition":transition,"emission":emission,"mixture":None}
    if isinstance(model,SequenceHMMMixture):
        ins=[]; trs=[]; ems=[]
        for k,c in enumerate(model.components,1):
            ins.extend({"component":k,"latent_state":s,"probability":float(c.initial_probs[i])} for i,s in enumerate(c.state_names)); trs.extend({"from_state":a,"to_state":b,"probability":float(c.transition_probs[i,j]),"component":k} for i,a in enumerate(c.state_names) for j,b in enumerate(c.state_names)); ems.extend({"latent_state":a,"observed_state":b,"probability":float(c.emission_probs[i,j]),"component":k} for i,a in enumerate(c.state_names) for j,b in enumerate(c.symbol_names))
        fit=pd.DataFrame([{"log_likelihood":model.log_likelihood,"aic":model.aic,"bic":model.bic,"n_parameters":model.n_parameters,"n_observations":model.n_observations,"iterations":model.iterations,"converged":model.converged}]); mix=pd.DataFrame({"component":np.arange(1,model.n_components+1),"weight":model.mixture_weights,"n_states":model.n_states});return {"fit":fit,"initial":pd.DataFrame(ins),"transition":pd.DataFrame(trs),"emission":pd.DataFrame(ems),"mixture":mix,"responsibilities":model.responsibilities}
    raise ValidationError("Unsupported HMM model object.")


def compare_sequence_hmms(*models:SequenceHMM|SequenceHMMMixture,**named_models:SequenceHMM|SequenceHMMMixture)->pd.DataFrame:
    if named_models:
        labels=list(named_models); mods=list(named_models.values())
        if models:mods=list(models)+mods;labels=[f"model_{i+1}" for i in range(len(models))]+labels
    else:mods=list(models);labels=[f"model_{i+1}" for i in range(len(mods))]
    if len(mods)<2:raise ValidationError("Supply at least two fitted HMMs.")
    if not all(isinstance(m,(SequenceHMM,SequenceHMMMixture)) for m in mods):raise ValidationError("All objects must be fitted sequence HMMs.")
    if len({m.n_observations for m in mods})!=1:raise ValidationError("HMM fit criteria are comparable only when models use the same number of observations.")
    ref=mods[0]
    if any(m.sequence_ids!=ref.sequence_ids or m.symbol_names!=ref.symbol_names or m.training_sequences!=ref.training_sequences or m.training_orders!=ref.training_orders for m in mods[1:]):raise ValidationError("HMM fit criteria are comparable only for identical training sequences, orders, and symbol coding.")
    rows=[{"model":lab,"class":"gp3_sequence_hmm" if isinstance(m,SequenceHMM) else "gp3_sequence_hmm_mixture","log_likelihood":m.log_likelihood,"aic":m.aic,"bic":m.bic,"n_parameters":m.n_parameters,"n_observations":m.n_observations,"converged":m.converged} for lab,m in zip(labels,mods,strict=True)]; out=pd.DataFrame(rows);out["delta_aic"]=out.aic-out.aic.min();out["delta_bic"]=out.bic-out.bic.min();return out.sort_values(["bic","aic","model"],kind="stable").reset_index(drop=True)
