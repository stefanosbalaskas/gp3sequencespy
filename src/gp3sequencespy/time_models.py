from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence
import numpy as np
import pandas as pd
from scipy.special import expit
from scipy.stats import norm
import matplotlib.pyplot as plt

from ._advanced import adv_data, scalar_logical, scalar_number
from ._exceptions import ModelFitError, ValidationError


def _require_time_backend():
    try:
        import patsy
        import statsmodels.api as sm
    except ImportError as exc:
        raise ModelFitError(
            "Time-varying sequence models require the optional 'time' dependencies. "
            "Install them with `pip install gp3sequencespy[time]` or "
            "`uv sync --extra time`."
        ) from exc
    return patsy, sm


@dataclass(slots=True)
class TimeVaryingSequenceModel:
    model: Any
    model_data: pd.DataFrame
    outcome: str
    target_state: str | None
    from_state: str | None
    to_state: str | None
    group_levels: list[str]
    participant_levels: list[str]
    time_range: tuple[float,float]
    k: int
    method: str
    include_random_effect: bool
    columns: dict[str,str]
    design_info: Any
    design_columns: list[str]


def _make_model_data(data, group_col, participant_id_col, sequence_id_col, order_col, state_col, time_col, outcome, target_state, from_state, to_state):
    x=adv_data(data,sequence_id_col,order_col,state_col,metadata_cols=[group_col,participant_id_col],missing_state_policy="error");w=x["data"]
    if time_col not in w.columns:raise ValidationError(f"Missing time column `{time_col}`.")
    if not pd.api.types.is_numeric_dtype(w[time_col]) or w[time_col].isna().any() or not np.isfinite(w[time_col].to_numpy(float)).all():raise ValidationError("The time column must contain finite, non-missing numeric values.")
    gv=w[group_col].astype("string");pv=w[participant_id_col].astype("string")
    if gv.isna().any() or gv.str.strip().eq("").any():raise ValidationError("Group values must not be missing or blank.")
    if pv.isna().any() or pv.str.strip().eq("").any():raise ValidationError("Participant identifiers must not be missing or blank.")
    if outcome=="state":
        md=pd.DataFrame({"outcome":(w[state_col].astype(str)==target_state).astype(int),"time":w[time_col].astype(float),"group":gv.astype(str),"participant":pv.astype(str)})
    else:
        rows=[]
        for sid in x["sequence_ids"]:
            p=w.loc[w[sequence_id_col].astype(str)==sid].reset_index(drop=True)
            for j in range(len(p)-1):
                rows.append({"outcome":int(str(p.loc[j,state_col])==from_state and str(p.loc[j+1,state_col])==to_state),"time":float(p.loc[j,time_col]),"group":str(p.loc[j,group_col]),"participant":str(p.loc[j,participant_id_col])})
        if not rows:raise ValidationError("No transitions are available for modelling.")
        md=pd.DataFrame(rows)
    groups=sorted(md.group.unique().tolist());parts=sorted(md.participant.unique().tolist())
    if len(groups)<2:raise ValidationError("At least two groups are required.")
    if md.time.nunique()<4:raise ValidationError("At least four distinct time values are required.")
    if md.outcome.nunique()<2:raise ValidationError("The target outcome has no variation.")
    return md,groups,parts


def _formula(groups,k,include_random_effect):
    # mgcv parity approximation: group main effects plus a separate cubic B-spline basis per group.
    terms=["C(group)"]
    for g in groups:
        safe=repr(g)
        terms.append(f"I(group == {safe}):bs(time, df={k}, degree=3, include_intercept=False)")
    if include_random_effect:terms.append("C(participant)")
    return "outcome ~ "+" + ".join(terms)


def fit_time_varying_sequence_model(data:Any,group_col:str,participant_id_col:str,sequence_id_col:str="sequence_id",order_col:str="sequence_order",state_col:str="state",time_col:str|None=None,outcome:str="state",target_state:str|None=None,from_state:str|None=None,to_state:str|None=None,k:int=5,method:str="REML",include_random_effect:bool=True)->TimeVaryingSequenceModel:
    if outcome not in {"state","transition"}:raise ValidationError("Invalid outcome.")
    for name,val in [("group_col",group_col),("participant_id_col",participant_id_col)]:
        if not isinstance(val,str) or not val:raise ValidationError(f"`{name}` must be a non-empty string.")
    time_col=order_col if time_col is None else time_col
    if not isinstance(time_col,str) or not time_col:raise ValidationError("`time_col` must be a non-empty string.")
    scalar_number(k,"k",3,integer=True);scalar_logical(include_random_effect,"include_random_effect")
    if outcome=="state" and (not isinstance(target_state,str) or not target_state):raise ValidationError("`target_state` must be a non-empty string.")
    if outcome=="transition" and (not isinstance(from_state,str) or not from_state or not isinstance(to_state,str) or not to_state):raise ValidationError("`from_state` and `to_state` must be non-empty strings.")
    md,groups,parts=_make_model_data(data,group_col,participant_id_col,sequence_id_col,order_col,state_col,time_col,outcome,target_state,from_state,to_state);k_used=min(int(k),int(md.time.nunique()-1))
    formula=_formula(groups,k_used,include_random_effect)
    patsy, sm = _require_time_backend()
    try:
        y,X=patsy.dmatrices(formula,md,return_type="dataframe")
        fit=sm.GLM(y,X,family=sm.families.Binomial()).fit()
    except Exception as e: raise ValidationError(f"Time-varying model fitting failed: {e}") from e
    return TimeVaryingSequenceModel(fit,md,outcome,target_state,from_state,to_state,groups,parts,(float(md.time.min()),float(md.time.max())),k_used,str(method),bool(include_random_effect),{"group":group_col,"participant":participant_id_col,"sequence_id":sequence_id_col,"order":order_col,"state":state_col,"time":time_col},X.design_info,list(X.columns))


def predict_time_varying_sequence_model(model:TimeVaryingSequenceModel,time:Sequence[float]|None=None,groups:Sequence[str]|None=None,level:float=.95)->pd.DataFrame:
    if not isinstance(model,TimeVaryingSequenceModel):raise ValidationError("`model` must be created by `fit_time_varying_sequence_model()`.")
    scalar_number(level,"level",.5,.999999)
    tv=np.linspace(*model.time_range,100) if time is None else np.asarray(time,float)
    if tv.ndim!=1 or not np.isfinite(tv).all():raise ValidationError("`time` must contain finite numeric values.")
    gs=model.group_levels if groups is None else [str(g) for g in groups]
    if any(g not in model.group_levels for g in gs):raise ValidationError("Unknown groups requested for prediction.")
    rows=[{"time":float(t),"group":g,"participant":model.participant_levels[0]} for g in gs for t in sorted(set(tv.tolist()))];grid=pd.DataFrame(rows)
    patsy, _ = _require_time_backend()
    try:X=patsy.build_design_matrices([model.design_info],grid,return_type="dataframe")[0]
    except Exception as e:raise ValidationError(f"Prediction design construction failed: {e}") from e
    params=np.asarray(model.model.params);cov=np.asarray(model.model.cov_params());eta=np.asarray(X)@params;se=np.sqrt(np.maximum(np.einsum("ij,jk,ik->i",np.asarray(X),cov,np.asarray(X)),0));z=norm.ppf(1-(1-level)/2)
    return pd.DataFrame({"time":grid.time.to_numpy(),"group":grid.group.to_numpy(),"estimate":expit(eta),"lower":expit(eta-z*se),"upper":expit(eta+z*se),"outcome":model.outcome})


def summarise_time_varying_sequence_model(model:TimeVaryingSequenceModel)->dict[str,Any]:
    if not isinstance(model,TimeVaryingSequenceModel):raise ValidationError("`model` must be created by `fit_time_varying_sequence_model()`.")
    # R mgcv exposes separate p/s tables. The Python approximation reports terms by origin.
    coef=pd.DataFrame({"coefficient":model.model.params,"std_error":model.model.bse,"z":model.model.tvalues,"p_value":model.model.pvalues}).reset_index(names="term")
    smooth=coef.loc[coef.term.str.contains("bs\\(time",regex=True)].reset_index(drop=True);param=coef.loc[~coef.term.str.contains("bs\\(time",regex=True)].reset_index(drop=True)
    md=pd.DataFrame([{"outcome":model.outcome,"target_state":model.target_state,"from_state":model.from_state,"to_state":model.to_state,"n_observations":len(model.model_data),"n_groups":len(model.group_levels),"n_participants":len(model.participant_levels),"k":model.k,"deviance_explained":float(1-model.model.deviance/model.model.null_deviance) if model.model.null_deviance else np.nan,"adjusted_r_squared":np.nan}])
    return {"metadata":md,"parametric_terms":param,"smooth_terms":smooth,"converged":bool(getattr(model.model,"converged",True)),"method":model.method}


def plot_time_varying_sequence_model(model:TimeVaryingSequenceModel,time:Sequence[float]|None=None,level:float=.95,show_interval:bool=True,ax=None,**kwargs):
    scalar_logical(show_interval,"show_interval");pred=predict_time_varying_sequence_model(model,time=time,level=level);ax=plt.gca() if ax is None else ax
    for g,p in pred.groupby("group",sort=False):
        p=p.sort_values("time");line=ax.plot(p.time,p.estimate,label=g,**kwargs)
        if show_interval:ax.fill_between(p.time,p.lower,p.upper,alpha=.2,color=line[0].get_color())
    ax.set_xlabel("Sequence time");ax.set_ylabel("Estimated probability");ax.legend();ax.gp3_data=pred
    return ax
