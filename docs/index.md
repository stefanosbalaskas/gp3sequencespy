<div class="gp3-home">

<section class="gp3-hero-v2">
  <div class="gp3-hero-v2__copy">
    <div class="gp3-kicker-row">
      <span class="gp3-kicker">gp3sequencespy 0.1.2</span>
      <span class="gp3-live-dot">Stable · PyPI</span>
    </div>
    <h1>See sequence structure.<br><span>Model what changes.</span></h1>
    <p class="gp3-hero-v2__lead">
      A parity-first Python toolkit for ordered categorical sequences and scanpaths:
      audit data, discover motifs, compare trajectories, model transitions and latent
      states, test group structure, and report every analytical choice transparently.
    </p>
    <div class="gp3-hero-v2__actions">
      <a class="md-button md-button--primary" href="quickstart/">Start in 5 minutes</a>
      <a class="md-button" href="method-map/">Choose a method</a>
      <a class="gp3-text-link" href="reference/">Browse the API <span aria-hidden="true">→</span></a>
    </div>
    <div class="gp3-trust-row" aria-label="Release validation summary">
      <span><b>81/81</b> R API counterparts</span>
      <span><b>292</b> tests</span>
      <span><b>100%</b> statement + branch coverage</span>
      <span><b>3/3</b> mutation smoke</span>
    </div>
  </div>

  <div class="gp3-hero-v2__visual" aria-label="Illustration of categorical sequences converging into analysis outputs">
    <div class="gp3-visual-window">
      <div class="gp3-visual-window__bar">
        <span></span><span></span><span></span>
        <small>sequence explorer</small>
      </div>
      <div class="gp3-lanes">
        <div class="gp3-lane"><b>S01</b><span class="a w2"></span><span class="b"></span><span class="c w2"></span><span class="d"></span></div>
        <div class="gp3-lane"><b>S02</b><span class="a"></span><span class="a"></span><span class="c"></span><span class="c w2"></span><span class="d"></span></div>
        <div class="gp3-lane"><b>S03</b><span class="d"></span><span class="c w2"></span><span class="b"></span><span class="a w2"></span></div>
        <div class="gp3-lane"><b>S04</b><span class="a w2"></span><span class="b w2"></span><span class="c"></span><span class="d"></span></div>
        <div class="gp3-lane"><b>S05</b><span class="b"></span><span class="c"></span><span class="b"></span><span class="d w2"></span><span class="a"></span></div>
      </div>
      <div class="gp3-visual-results">
        <div><small>distance</small><strong>0.28</strong></div>
        <div><small>motifs</small><strong>12</strong></div>
        <div><small>states</small><strong>4</strong></div>
      </div>
      <div class="gp3-visual-caption">states → structure → evidence</div>
    </div>
  </div>
</section>

<div class="gp3-install-strip">
  <div>
    <span class="gp3-install-label">Install stable</span>
    <code>pip install gp3sequencespy==0.1.2</code>
  </div>
  <div class="gp3-install-links">
    <a href="https://pypi.org/project/gp3sequencespy/">PyPI</a>
    <a href="https://github.com/stefanosbalaskas/gp3sequencespy/releases/tag/v0.1.2">Release</a>
    <a href="https://doi.org/10.5281/zenodo.22166449">Zenodo</a>
  </div>
</div>

<section class="gp3-section-intro">
  <span class="gp3-section-number">01</span>
  <div>
    <p class="gp3-overline">Start from the research question</p>
    <h2>Choose the analysis by what you need to learn.</h2>
    <p>Move from a substantive question to an auditable method instead of starting from a function name.</p>
  </div>
</section>

<div class="gp3-question-grid">
  <a class="gp3-question-card" href="articles/sequence-data-validation-and-preparation/">
    <span class="gp3-question-card__index">01</span><div class="gp3-question-card__icon">✓</div>
    <h3>Can I trust the sequence data?</h3><p>Audit order, missing states, duplicated positions, duration fields, metadata, and explicit preparation policies.</p>
    <span class="gp3-question-card__link">Validate &amp; prepare →</span>
  </a>
  <a class="gp3-question-card" href="examples/">
    <span class="gp3-question-card__index">02</span><div class="gp3-question-card__icon">≋</div>
    <h3>What patterns recur?</h3><p>Summarise paths, occupancy, consensus, contiguous motifs, non-contiguous subsequences, and transition structure.</p>
    <span class="gp3-question-card__link">Describe structure →</span>
  </a>
  <a class="gp3-question-card" href="articles/distances-clustering-and-stability/">
    <span class="gp3-question-card__index">03</span><div class="gp3-question-card__icon">△</div>
    <h3>Which sequences are similar?</h3><p>Use edit, LCS, optimal-matching, or transition-profile distances, then cluster and test stability.</p>
    <span class="gp3-question-card__link">Compare trajectories →</span>
  </a>
  <a class="gp3-question-card" href="articles/transition-networks-and-higher-order-models/">
    <span class="gp3-question-card__index">04</span><div class="gp3-question-card__icon">↗</div>
    <h3>How do states connect?</h3><p>Build transition networks, inspect centrality and communities, fit higher-order models, and predict next states.</p>
    <span class="gp3-question-card__link">Model transitions →</span>
  </a>
  <a class="gp3-question-card" href="articles/latent-models-and-optional-adapters/">
    <span class="gp3-question-card__index">05</span><div class="gp3-question-card__icon">◇</div>
    <h3>Is there latent structure?</h3><p>Fit categorical, mixture, multichannel, and covariate-dependent HMM workflows with explicit convergence boundaries.</p>
    <span class="gp3-question-card__link">Fit latent models →</span>
  </a>
  <a class="gp3-question-card" href="articles/sequence-inference-and-randomization/">
    <span class="gp3-question-card__index">06</span><div class="gp3-question-card__icon">∴</div>
    <h3>Do groups differ defensibly?</h3><p>Declare the comparison design and use design-aware randomization rather than over-interpreting descriptive differences.</p>
    <span class="gp3-question-card__link">Run inference →</span>
  </a>
</div>

<div class="gp3-method-cta">
  <div><span>Not sure which route fits?</span><strong>Use the method map to move from question → assumptions → function family.</strong></div>
  <a class="md-button" href="method-map/">Open method map</a>
</div>

<section class="gp3-section-intro">
  <span class="gp3-section-number">02</span>
  <div><p class="gp3-overline">A defensible workflow</p><h2>From raw events to a reportable result.</h2><p>Every stage keeps assumptions and transformations visible.</p></div>
</section>

<div class="gp3-flow-v2">
  <div><b>01</b><strong>Audit</strong><span>integrity · order · missingness</span></div><i>→</i>
  <div><b>02</b><strong>Prepare</strong><span>explicit transformation policy</span></div><i>→</i>
  <div><b>03</b><strong>Describe</strong><span>states · paths · motifs</span></div><i>→</i>
  <div><b>04</b><strong>Compare</strong><span>distance · groups · stability</span></div><i>→</i>
  <div><b>05</b><strong>Model</strong><span>transitions · networks · HMMs</span></div><i>→</i>
  <div><b>06</b><strong>Report</strong><span>plots · parameters · audit trail</span></div>
</div>

<div class="gp3-code-stage">
  <div class="gp3-code-stage__copy">
    <h3>A small API, composed into a full workflow</h3>
    <p>The same prepared sequence object can feed descriptive summaries, distances, networks, latent models, inference, and visualisation.</p>
    <a class="gp3-inline-arrow" href="quickstart/">Quickstart →</a>
  </div>
  <div class="gp3-code-stage__code"><pre><code class="language-python">import gp3sequencespy as g

validation = g.validate_sequence_data(data)
prepared = g.prepare_sequence_data(data)

states = g.summarise_sequence_states(prepared.data)
distance = g.compute_sequence_distance(
    prepared.data,
    method="lcs",
)
network = g.create_transition_network(
    prepared.data,
    normalise="from",
)</code></pre></div>
</div>

<section class="gp3-section-intro">
  <span class="gp3-section-number">03</span>
  <div><p class="gp3-overline">See the structure</p><h2>Visual outputs that stay connected to the method.</h2><p>Use plots as analytical summaries, not decoration. Each gallery entry links back to the generating function and interpretation notes.</p></div>
</section>

<div class="gp3-plot-showcase">
  <a href="plots/#sequence-index" class="gp3-plot-tile gp3-plot-tile--wide"><img src="assets/figures/sequence-index.svg" alt="Illustrative sequence index plot"><span><b>Sequence index</b><small>Inspect complete paths and between-sequence structure</small></span></a>
  <a href="plots/#state-distribution" class="gp3-plot-tile"><img src="assets/figures/state-distribution.svg" alt="Illustrative state distribution plot"><span><b>State distribution</b><small>See occupancy change over sequence position</small></span></a>
  <a href="plots/#distance-heatmap" class="gp3-plot-tile"><img src="assets/figures/distance-heatmap.svg" alt="Illustrative sequence distance heatmap"><span><b>Distance heatmap</b><small>Inspect similarity and cluster separation</small></span></a>
  <a href="plots/#transition-network" class="gp3-plot-tile gp3-plot-tile--wide"><img src="assets/figures/transition-network.svg" alt="Illustrative transition network"><span><b>Transition network</b><small>Map state-to-state structure and directional flow</small></span></a>
</div>
<div class="gp3-center-action"><a class="md-button" href="plots/">Explore the full plot gallery</a></div>

<section class="gp3-section-intro">
  <span class="gp3-section-number">04</span>
  <div><p class="gp3-overline">Evidence, not just features</p><h2>Built around explicit scientific contracts.</h2><p>The Python implementation is tested against a frozen R reference and exposes its translation boundaries instead of hiding them.</p></div>
</section>

<div class="gp3-evidence-shell">
  <div class="gp3-evidence-main">
    <span class="gp3-evidence-label">Parity-first implementation</span>
    <h3>Frozen behavior. Audited translation. Python-native integration.</h3>
    <p><code>gp3sequencespy</code> implements the frozen <strong>gp3sequences 0.3.0</strong> public contract. Public signatures, translated test blocks, deterministic oracles, and deliberate R→Python boundaries are documented as release evidence.</p>
    <div class="gp3-evidence-links"><a href="parity/">Parity &amp; validation →</a><a href="reproducibility/">Reproducibility →</a><a href="reporting/">Reporting guide →</a></div>
  </div>
  <div class="gp3-evidence-metrics">
    <div><strong>81 / 81</strong><span>public R counterparts exported</span></div><div><strong>81 / 81</strong><span>public signatures audited</span></div>
    <div><strong>130 / 130</strong><span>frozen R test blocks translated</span></div><div><strong>15</strong><span>methodology articles</span></div>
  </div>
</div>

<div class="gp3-ribbon-grid">
  <div><span class="gp3-ribbon-icon">R→Py</span><h3>Coming from gp3sequences in R?</h3><p>Use the translation guide to map function names, return structures, plotting conventions, and documented semantic differences.</p><a href="r-to-python/">Open the R → Python guide →</a></div>
  <div><span class="gp3-ribbon-icon">API</span><h3>Already know the method?</h3><p>Jump directly to the frozen public API and inspect signatures, parameters, return objects, and implementation notes.</p><a href="reference/api/">Browse all public functions →</a></div>
</div>

<section class="gp3-guardrail-v2">
  <div class="gp3-guardrail-v2__mark">!</div>
  <div><span>Interpretation boundary</span><h2>Sequence structure is not a psychological state.</h2><p>Sequence structure does not independently establish attention, cognition, emotion, comprehension, personality, intention, deception, diagnosis, or causality. Observational group contrasts remain associational unless a defensible randomized design supports causal interpretation.</p></div>
</section>

<section class="gp3-final-cta">
  <div><span class="gp3-overline">Ready to analyse a sequence?</span><h2>Start small. Keep every decision visible.</h2><p>Install 0.1.2, validate a three-column sequence table, and expand only when the research question requires it.</p></div>
  <div class="gp3-final-cta__actions"><a class="md-button md-button--primary" href="quickstart/">Open quickstart</a><a class="md-button" href="examples/">See worked examples</a></div>
</section>

</div>
