import numpy as np
import pandas as pd
import pytest

from gp3sequencespy import (
    audit_sequence_data, validate_sequence_data, prepare_sequence_data,
    encode_sequence_data, summarise_sequence_states,
    summarise_sequence_transitions, format_sequence_paths,
    extract_sequence_ngrams, summarise_sequence_motifs,
)


def seqdata():
    return pd.DataFrame({
        "id": ["s1"]*3+["s2"]*3,
        "position": [1,2,3,1,2,3],
        "state": ["home","search","product","home","category","product"],
        "duration_ms": [100,200,300,120,180,260],
        "participant": ["p1"]*3+["p2"]*3,
    })


def test_validation_and_prepare_contract():
    d=seqdata()
    a=audit_sequence_data(d,"id","position","state","duration_ms",["participant"])
    assert list(a.columns)==["sequence_id","row","column","issue_code","severity","value","message","action"]
    assert len(a)==0
    v=validate_sequence_data(d,"id","position","state")
    assert v.valid and v.status=="pass" and v.n_sequences==2 and v.n_rows==6
    shuffled=d.iloc[[5,1,0,4,2,3]].reset_index(drop=True)
    p=prepare_sequence_data(shuffled,"id","position","state","duration_ms",["participant"])
    assert p.status=="pass"
    assert p.data is not None
    assert list(p.data.sequence_id)==["s1"]*3+["s2"]*3
    assert list(p.data.sequence_order)==[1,2,3,1,2,3]
    assert list(p.data.original_row)==[3,2,5,6,4,1]


def test_encoding_state_transition_path_contracts():
    d=pd.DataFrame({
        "id":["s1"]*4+["s2"]*3,
        "position":[1,2,3,4,1,2,3],
        "state":["A","B","A","C","B","C","A"],
        "duration_ms":[1,2,3,4,2,2,6],
        "group":["g1"]*4+["g2"]*3,
    })
    enc=encode_sequence_data(d,"id","position","state")
    assert list(enc.dictionary.state)==["A","B","C"]
    assert list(enc.dictionary.state_code)==["S1","S2","S3"]
    s=summarise_sequence_states(d,"id","position","state","duration_ms",["group"])
    s1a=s.by_sequence.query("sequence_id=='s1' and state=='A'").iloc[0]
    assert s1a.n_observations==2
    assert s1a.observation_proportion==pytest.approx(.5)
    assert s1a.duration_sum==pytest.approx(4)
    t=summarise_sequence_transitions(d,"id","position","state",["group"])
    ab=t.by_sequence.query("sequence_id=='s1' and from_state=='A' and to_state=='B'").iloc[0]
    assert ab.n_transitions==1
    assert ab.sequence_transition_proportion==pytest.approx(1/3)
    assert ab.origin_transition_proportion==pytest.approx(.5)
    paths=format_sequence_paths(d,"id","position","state")
    assert paths.paths.loc[0,"path"]=="A > B > A > C"


def motifdata():
    return pd.DataFrame({
        "id":["s1"]*5+["s2"]*4,
        "position":[1,2,3,4,5,1,2,3,4],
        "state":["A","B","A","B","A","A","B","A","C"],
        "group":["g1"]*5+["g2"]*4,
    })


def test_motif_contracts():
    e=extract_sequence_ngrams(motifdata(),"id","position","state",metadata_cols=["group"],min_length=2,max_length=3)
    assert len(e.occurrences)==12
    assert list(e.sequences.n_candidate_occurrences)==[7,5]
    aba=e.occurrences.query("sequence_id=='s1' and motif=='A > B > A'")
    assert list(aba.start_index)==[1,3]
    assert list(aba.occurrence_index)==[1,2]
    s=summarise_sequence_motifs(e)
    aba2=s.overall.query("motif=='A > B > A'").iloc[0]
    assert aba2.n_occurrences==3 and aba2.n_sequences==2
    assert aba2.sequence_prevalence==pytest.approx(1)
    assert aba2.occurrence_share==pytest.approx(3/12)
    dis=extract_sequence_ngrams(motifdata(),"id","position","state",min_length=3,max_length=3,overlap="disallow")
    assert len(dis.occurrences.query("motif=='A > B > A'"))==2


def _advanced_data():
    paths = {
        's01':['A','B','C','D','D'], 's02':['A','B','C','D','C'],
        's03':['A','B','B','C','D'], 's04':['A','C','C','D','D'],
        's05':['D','C','B','A','A'], 's06':['D','C','B','A','B'],
        's07':['D','C','C','B','A'], 's08':['D','B','B','A','A'],
    }
    rows=[]
    for i,(sid,path) in enumerate(paths.items(),1):
        g='g1' if i<=4 else 'g2'
        rows += [{'sequence_id':sid,'sequence_order':j,'state':s,'group':g,'participant_id':f'p{i}','weight':1} for j,s in enumerate(path,1)]
    return pd.DataFrame(rows)


def test_consensus_and_group_comparison_contracts():
    from gp3sequencespy.consensus import create_consensus_sequence, summarise_consensus_agreement, format_consensus_sequence, compare_sequence_groups
    data=_advanced_data()
    con=create_consensus_sequence(data,group_cols='group',tie_method='first')
    assert len(con)==10
    assert (con['support_n']==4).all()
    assert con['agreement'].between(.5,1).all()
    assert len(summarise_consensus_agreement(con,'overall'))==1
    assert len(summarise_consensus_agreement(con,'group'))==2
    assert len(format_consensus_sequence(con,include_agreement=True))==2
    cmp=compare_sequence_groups(data,'group')
    assert cmp.groups['n_sequences'].tolist()==[4,4]
    assert len(cmp.length_summary)==2
    assert not any('p_value' in c or 'statistic' in c for c in cmp.state_contrasts.columns)


def test_consensus_ties_and_zero_weights():
    from gp3sequencespy.consensus import create_consensus_sequence
    d=pd.DataFrame({'sequence_id':['s1','s2'],'sequence_order':[1,1],'state':['B','A']})
    assert create_consensus_sequence(d,tie_method='first',state_levels=['A','B']).iloc[0].consensus_state=='A'
    assert create_consensus_sequence(d,tie_method='last',state_levels=['A','B']).iloc[0].consensus_state=='B'
    assert pd.isna(create_consensus_sequence(d,tie_method='missing',state_levels=['A','B']).iloc[0].consensus_state)
    assert create_consensus_sequence(d,tie_method='all',state_levels=['A','B']).iloc[0].consensus_state=='A | B'
    w=pd.DataFrame({'sequence_id':['s1','s2'],'sequence_order':[1,1],'state':['A','B'],'weight':[1,0]})
    c=create_consensus_sequence(w,weight_col='weight')
    assert c.iloc[0].support_n==1 and c.iloc[0].support_weight==1


def test_sequence_distances_and_clustering():
    from gp3sequencespy import compute_sequence_distance, summarise_sequence_distance, cluster_sequences, validate_sequence_clusters, extract_representative_sequences, create_sequence_cluster_ensemble
    d=_advanced_data()
    for method in ['levenshtein','lcs','optimal_matching','transition']:
        x=compute_sequence_distance(d,method=method)
        assert np.allclose(x.matrix,x.matrix.T)
        assert np.allclose(np.diag(x.matrix),0)
    x=compute_sequence_distance(d,method='lcs')
    sm=summarise_sequence_distance(x)
    assert sm['overall'].iloc[0].n_sequences==8 and sm['overall'].iloc[0].n_pairs==28
    h=cluster_sequences(x,2)
    assert len(h.assignments)==8 and len(h.medoids)==2
    v=validate_sequence_clusters(h)
    assert v['overall'].iloc[0].n_clusters==2
    reps=extract_representative_sequences(h)
    assert len(reps)==2
    p=cluster_sequences(x,2,method='pam')
    ens=create_sequence_cluster_ensemble(h,p,k=2)
    assert ens.coassociation.shape==(8,8)


def test_distance_normalisation_and_bootstrap_reproducible():
    from gp3sequencespy import compute_sequence_distance, bootstrap_sequence_clusters
    d=_advanced_data(); a=compute_sequence_distance(d,method='lcs'); b=compute_sequence_distance(d,method='lcs',normalise='max_length')
    assert np.all(b.matrix<=a.matrix+1e-12)
    x=bootstrap_sequence_clusters(a,2,n_boot=5,seed=17)
    y=bootstrap_sequence_clusters(a,2,n_boot=5,seed=17)
    assert np.allclose(x.pairwise_stability.to_numpy(),y.pairwise_stability.to_numpy(),equal_nan=True)


def test_transition_network_markov_and_bootstrap():
    from gp3sequencespy import create_transition_network, summarise_transition_centrality, detect_transition_communities, fit_higher_order_transition_model, predict_next_state, bootstrap_transition_network
    d=_advanced_data(); n=create_transition_network(d,normalise='from')
    assert np.allclose(n.groupby('context').weight.sum().to_numpy(),1)
    ns=create_transition_network(d,include_self=False); assert not (ns.from_state==ns.to_state).any()
    n2=create_transition_network(d,order=2,normalise='from'); assert n2.from_state.isna().all() and n2.context.str.contains(' > ',regex=False).all()
    c=summarise_transition_centrality(create_transition_network(d,normalise='count')); assert np.isclose(c.pagerank.sum(),1)
    assert detect_transition_communities(n,seed=9).equals(detect_transition_communities(n,seed=9))
    m=fit_higher_order_transition_model(d,order=3,smoothing=.5,backoff=True); p=predict_next_state(m,['A','B','C']); assert np.isclose(p.probability.sum(),1) and p.used_order.iloc[0]<=3
    u=predict_next_state(m,['Z']); assert (u.used_order==0).all()
    b1=bootstrap_transition_network(d,n_boot=5,seed=17); b2=bootstrap_transition_network(d,n_boot=5,seed=17); pd.testing.assert_frame_equal(b1,b2)


def test_panel_workflow():
    from gp3sequencespy import prepare_sequence_panel, summarise_sequence_panel, compare_sequence_panel_changes
    rows=[]
    for p in range(1,5):
        for occ in [1,2]:
            sid=f'p{p}_w{occ}'; path=['A','B','C'] if occ==1 else ['A','C','C']
            rows += [{'participant_id':f'p{p}','occasion':occ,'sequence_id':sid,'sequence_order':i,'state':s} for i,s in enumerate(path,1)]
    d=pd.DataFrame(rows); panel=prepare_sequence_panel(d,'participant_id','occasion'); sm=summarise_sequence_panel(panel)
    assert len(panel.index)==8 and sm['n_panels']==4 and sm['n_occasions']==2
    ch=compare_sequence_panel_changes(panel,method='lcs'); assert len(ch)==4 and (ch.distance>=0).all()


def test_noncontiguous_subsequences():
    from gp3sequencespy import extract_sequence_subsequences, summarise_sequence_subsequences, filter_sequence_subsequences, compare_sequence_subsequences
    d=_advanced_data(); o=extract_sequence_subsequences(d,metadata_cols='group',min_length=2,max_length=3,max_gap=2,max_span=4)
    assert len(o)>0 and o.subsequence_length.isin([2,3]).all() and (o.max_observed_gap<=2).all() and (o.span<=4).all()
    s=summarise_sequence_subsequences(o); assert s.sequence_prevalence.between(0,1).all(); f=filter_sequence_subsequences(s,min_sequences=2,top_n=5,ties='exclude'); assert len(f)<=5
    c=compare_sequence_subsequences(o,'group'); assert {'p_value','p_adjusted'}.issubset(c.columns) and (c.p_adjusted>=c.p_value-1e-12).all()


def test_hmm_core_and_mixture():
    from gp3sequencespy import fit_sequence_hmm, decode_sequence_states, summarise_sequence_hmm, compare_sequence_hmms, fit_sequence_hmm_mixture
    d=_advanced_data(); m=fit_sequence_hmm(d,2,max_iter=20,seed=11)
    assert np.isclose(m.initial_probs.sum(),1) and np.allclose(m.transition_probs.sum(1),1) and np.allclose(m.emission_probs.sum(1),1) and np.isfinite(m.log_likelihood)
    dec=decode_sequence_states(m); assert len(dec)==len(d) and dec.posterior_probability.between(0,1).all()
    m3=fit_sequence_hmm(d,3,max_iter=10,seed=4); cmp=compare_sequence_hmms(two=m,three=m3); assert len(cmp)==2 and {'delta_aic','delta_bic','converged'}.issubset(cmp.columns)
    mix=fit_sequence_hmm_mixture(d,2,2,max_iter=8,inner_initial_iter=3,seed=21); probs=mix.responsibilities[['component_1','component_2']].to_numpy(); assert np.allclose(probs.sum(1),1)
    md=decode_sequence_states(mix); assert len(md)==len(d) and set(md.component).issubset({1,2})


def test_design_aware_inference():
    from gp3sequencespy import declare_sequence_comparison_design,test_sequence_group_difference,bootstrap_sequence_group_difference,summarise_sequence_group_inference
    d=_advanced_data(); design=declare_sequence_comparison_design('group','participant_id','observational'); inf=test_sequence_group_difference(d,design,metric='state_prevalence',target_state='A',n_permutations=49,seed=4)
    assert len(inf.unit_data)==8 and 0<=inf.estimate.p_value.iloc[0]<=1 and 'Associational' in inf.interpretation
    inf=bootstrap_sequence_group_difference(inf,n_boot=49,seed=5); sm=summarise_sequence_group_inference(inf); assert len(sm['bootstrap_interval'])==1


def test_multichannel_hmm():
    from gp3sequencespy import fit_multichannel_sequence_hmm,decode_multichannel_sequence_states,summarise_multichannel_sequence_hmm
    d=_advanced_data().copy(); d['channel_context']=np.tile(['x','x','y','y','z'],8)
    m=fit_multichannel_sequence_hmm(d,2,['state','channel_context'],max_iter=4,seed=11); assert m.transition_probs.shape==(2,2) and len(m.emission_probs)==2 and np.isfinite(m.log_likelihood)
    dec=decode_multichannel_sequence_states(m);assert len(dec)==len(d);sm=summarise_multichannel_sequence_hmm(m);assert {'fit','initial','transition','emission'}<=sm.keys()

def test_covariate_hmm_contract():
    import gp3sequencespy as g
    d=pd.DataFrame({
        "sequence_id":np.repeat([f"s{i}" for i in range(1,9)],5),
        "sequence_order":list(range(1,6))*8,
        "state":list("ABCBA")*8,
        "condition_numeric":np.repeat(np.repeat([0,1],4),5),
    })
    fit=g.fit_covariate_sequence_hmm(d,2,initial_covariate_cols=["condition_numeric"],transition_covariate_cols=["condition_numeric"],max_iter=3,inner_maxit=10,seed=12)
    assert fit.emission_probs.shape==(2,3)
    assert np.isfinite(fit.log_likelihood)
    pred=g.predict_covariate_transition_probabilities(fit,pd.DataFrame({"condition_numeric":[0,1]}))
    assert len(pred)==8 and {"row","from_state","to_state","probability"}<=set(pred)
    dec=g.decode_covariate_sequence_states(fit)
    assert len(dec)==len(d)
    sm=g.summarise_covariate_sequence_hmm(fit)
    assert {"fit","initial_coefficients","transition_coefficients","emission"}<=set(sm)

def test_time_varying_model_contract():
    import gp3sequencespy as g
    rng=np.random.default_rng(101);rows=[]
    for i in range(24):
        group="g1" if i<12 else "g2"
        for t in range(1,13):
            lp=-.4+.06*t+.35*(group=="g2")*np.sin(t/3);rows.append({"participant_id":f"p{i+1}","sequence_id":f"p{i+1}","sequence_order":t,"state":"A" if rng.random()<1/(1+np.exp(-lp)) else "B","group":group})
    d=pd.DataFrame(rows);fit=g.fit_time_varying_sequence_model(d,"group","participant_id",target_state="A",k=3,include_random_effect=False)
    pred=g.predict_time_varying_sequence_model(fit,time=[1,6,12]);assert len(pred)==6 and pred.estimate.between(0,1).all();sm=g.summarise_time_varying_sequence_model(fit);assert {"metadata","smooth_terms","converged"}<=set(sm);ax=g.plot_time_varying_sequence_model(fit,time=[1,6,12]);assert hasattr(ax,"gp3_data")

def test_motif_position_and_plot_contracts():
    import gp3sequencespy as g
    d=pd.DataFrame({"id":["s1"]*5+["s2"]*4+["s3"]*3,"position":[1,2,3,4,5,1,2,3,4,1,2,3],"state":list("ABABC")+list("ABCB")+list("BAB"),"group":["g1"]*9+["g2"]*3})
    ex=g.extract_sequence_ngrams(d,"id","position","state",metadata_cols=["group"],min_length=2,max_length=3)
    p=g.summarise_sequence_motif_positions(ex,"start","absolute");ab=p.summary.loc[p.summary.motif=="A > B"].iloc[0];assert ab.n_occurrences==4 and ab.n_sequences==3 and ab.mean_position==1.75
    pr=g.summarise_sequence_motif_positions(ex,"start","relative",by="group");fmt=g.format_sequence_motif_positions(pr,digits=1,position_units="percent");assert "rank" in fmt["table"] and set(fmt["table"].position_unit)=={"percent"}
    ax=g.plot_sequence_motifs(g.summarise_sequence_motifs(ex),metric="n_occurrences",top_n=3,ties="first");assert len(ax.gp3_data)==3
    ax2=g.plot_sequence_motif_positions(ex,position="centre",scale="relative",top_n=2);assert len(ax2.gp3_motif_table)==2 and ax2.gp3_data.position_value.between(0,1).all()
