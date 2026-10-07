# Fact base: what World Labs' public pages describe, and the physical-AI literature around a geophysicist's skills

> A fact base of public statements and literature. It is not an assessment of any company's products.

Compiled 2026-10-03 (fetch date for every URL below). Purpose: a fact base for the quotations and references used on the site. The objective is to start from open problems World Labs describes and see where seismic-imaging skills (migration, tomography, FWI, multiples, uncertainty) could contribute complementary ideas to spatial intelligence and robots, and where World Labs or others already cover it.

## 0. Method and limits (read first)

- **Part A quotes** came from the WebFetch tool, which extracts text through a small summarising model. Treat quotes as high-confidence but not byte-exact. The two quotes this project leans on most were fetched twice with targeted "does this exact phrase appear?" prompts (see A-12, A-17, A-23). Re-verify any quote in a document you publish.
- **Part B references** were checked against the arXiv API (`export.arxiv.org`) or Crossref: exact title, first author and date were read from the returned metadata. Abstracts were read in full for the works marked **[abs]**. For others the description is **title-level only** and says so. No ID was taken from memory without a metadata check.
- **Negative searches** ("not found") mean: the arXiv API returned zero results for that conjunction of abstract terms on 2026-10-03. It does not mean the work does not exist (conference-only, journal-only and industry work is under-covered; geophysics literature in SEG/Geophysics journals was not searched by this fork).
- Company statements are **company-reported**. Nothing from World Labs was independently reproduced here, except where marked "verified locally".

## Part A. What World Labs' public pages describe

This part records, in short attributed excerpts and paraphrases, what World Labs' public pages describe, so that this project can start from World Labs' own stated open problems and never misstate its work. Row numbers are kept stable for cross-references; rows for topics a page does not cover are not listed, because topics outside a page's scope are not treated as shortcomings.

### A1. Claim table

| # | Topic | What the page says (short excerpt or paraphrase) | URL | Status |
|---|---|---|---|---|
| A-1 | Marble inputs | Marble can create 3D worlds from text, images, video, or coarse 3D layouts (12 Nov 2025). | worldlabs.ai/blog/marble-world-model | company-reported |
| A-2 | Marble multi-image | Different prompt images can be used for different parts of a world and stitched into one world. | same | company-reported |
| A-3 | Marble exports | Gaussian splats are described as the highest-fidelity representation; collider meshes are for coarse physics simulation; high-quality meshes are also offered. | same | company-reported |
| A-5 | Atlas fills in views | When parts of the world are not visible in the input views, "Atlas imagines a plausible way to fill in the gaps by drawing from its rich world knowledge" (1 Sep 2026). | worldlabs.ai/blog/atlas | company-reported |
| A-6 | Atlas and robotics | The post describes generating the RGB and depth data a simulated robot's sensors would observe, and presents Atlas as a world simulator for scaling real-to-sim for navigation and manipulation. | same | company-reported |
| A-7 | Atlas availability | Atlas is entering early access with select partners. | same | company-reported |
| A-8 | Atlas evaluation | Reports mean absolute-relative pointmap error on several public datasets, with baselines reproduced by World Labs. | same | company-reported, not independently reproduced |
| A-10 | Taxonomy: simulator contract | Contrasts a renderer's visual contract with a simulator's structural contract: geometry that "holds up under inspection", physics that respects Newton's laws, and dynamics consistent with the laws of physics (3 Jun 2026). | worldlabs.ai/blog/taxonomy-of-world-models | company-reported; re-verified by a second fetch |
| A-11 | Taxonomy: definitions | Defines a simulator as a geometrically, physically or dynamically faithful representation of the world that humans and programs can compute on and interact with. | same | company-reported |
| A-12 | Taxonomy: open problems | Lists the scarcity of 3D data with geometry, materials and physical annotations, the sim-to-real gap, and the cost of multi-physics simulation as open problems, and notes that "AI-generated geometry can look correct while containing self-intersections or wrong scale that produce nonsensical physics." | same | company-reported |
| A-13 | Taxonomy: validation | Notes that existing approaches have not yet been validated at the complexity, variability or duration that real-world deployment demands. | same | company-reported |
| A-15 | R2S2R claims | Describes learning manipulation tasks with no real-world training data and predicting through simulation which policies will succeed in the real world (28 Jul 2026). | worldlabs.ai/blog/real-to-sim-to-real | company-reported |
| A-16 | R2S2R evaluation | Each checkpoint is evaluated on 2,000 simulated and 100 real-world trials, split into in-distribution and out-of-distribution; metrics are policy ranking, success/failure patterns and sim/hardware correlation. | same | company-reported; methodology partly disclosed |
| A-17 | R2S2R uncertainty | States that "Object shape, weight, and friction may be uncertain", and that cameras and robots can differ from their specifications; different representations and modelling techniques are chosen per task. | same | company-reported |
| A-18 | RTFM | A learned renderer that generates video in real time as the user interacts; input frames become network activations (a KV cache) that implicitly represent the world; designed to run on a single H100 GPU; future work includes dynamic worlds and interaction (16 Oct 2025). | worldlabs.ai/blog/rtfm | company-reported |
| A-19 | SceniX | An acquisition announcement (21 Jul 2026) that points to technical posts to come. | worldlabs.ai/blog/scenix | company-reported |
| A-21 | World API | Inputs include text, images, panoramas, multi-view inputs and video; the model list includes `marble-1.1-plus`, `marble-1.1`, `marble-1.0` and `marble-1.0-draft`; Atlas and RTFM are not in the list (21 Jan 2026). | docs.worldlabs.ai/api/models.md ; /api/reference/index.md | documentation |
| A-22 | Multi-image docs | Direction mode takes up to four images labelled front, back, left and right; auto layout takes up to eight images captured close together with different viewing directions; a 360° panorama gives the most accurate single-space layout. | docs.worldlabs.ai/marble/create/prompt-guides/multi-image-prompt.md | documentation |
| A-23 | Unseen areas | "Parts of the scene the cameras never see, such as behind closed doors, around solid walls, or up a staircase, are generated plausibly to keep the world explorable, so they won't match a real floor plan of those hidden areas." | same | documentation |
| A-24 | Expand | A feature for improving low-fidelity regions of a world; not available for worlds generated with Marble 1.1 Plus. | docs.worldlabs.ai/marble/create/prompt-guides/expand.md | documentation |
| A-25 | Panorama and Chisel | Panorama prompts give the model a full 360° view; Chisel creates detailed worlds from coarse 3D blocking plus a text prompt (GLB or FBX input). | .../pano-prompt.md ; .../chisel-basics.md | documentation |
| A-26 | Mesh exports | Collider meshes (about 100-200k triangles) are described as optimized for physics interactions and for simple physics in games; high-quality meshes have about 600k textured or 1M vertex-coloured triangles; the page lists the kinds of artifact to expect and notes that meshes are derived from the world. | docs.worldlabs.ai/marble/export/mesh.md ; /export/specs.md | documentation |
| A-27 | Metric scale | `metric_scale_factor` converts raw generated asset units to meters; `ground_plane_offset` places the metric ground plane at y = 0; SPZ assets use the `marble_raw_opencv` convention. | docs.worldlabs.ai/api/rendering-spz.md | documentation |
| A-29 | Depth-to-RGB | Generates an RGB panorama from a full 360° equirectangular depth panorama (2:1), synthesizing textures guided by that geometry. | docs.worldlabs.ai/api/reference/pano/depth_to_rgb.md | documentation |
| A-30 | Spark | Open source under the MIT licence (Copyright 2025 World Labs Technologies, Inc., checked in a local clone); the Spark 2.0 post describes a continuous level-of-detail splat tree, the .RAD format and a compact .SPZ (14 Apr 2026). | worldlabs.ai/blog/spark-2.0 ; sparkjs.dev/docs | licence verified locally; post is company-reported |

### A2. What World Labs' pages describe (topics used as starting points)

| Topic | What the pages describe |
|---|---|
| Uncertainty | The real-to-sim-to-real post describes uncertain shape, weight and friction (A-17); the multi-image guide says unseen areas are generated plausibly (A-23); Expand improves low-fidelity regions (A-24). |
| Provenance (seen versus generated) | The multi-image guide describes how unseen areas are handled (A-23). |
| Physics | Collider meshes for simple physics (A-26); a simulator contract in the taxonomy post (A-10); Atlas as a world simulator (A-6); sim/real correlation in the real-to-sim-to-real post (A-16). |
| Scale | A conversion factor to meters and a ground-plane offset (A-27). |
| Geometry quality | The mesh page describes the kinds of artifact to expect and that meshes derive from the world (A-26); the taxonomy post names wrong scale and self-intersections as open problems for generated geometry (A-12). |

## Part B. Existing literature (verified this session)

All IDs below are arXiv unless a DOI is given. **[abs]** = abstract read in full this session; otherwise title-level only.

### B-table

| Topic | Existing works (verified) | What they do | Relation to geophysics skills | Open gap? | Evidence |
|---|---|---|---|---|---|
| B1a Physical-parameter inversion from video | PhysGaussian 2311.12198 [abs]; PhysDreamer 2404.13026 [abs]; PAC-NeRF 2303.05512 [abs]; Spring-Gaus 2403.09434 [abs]; GIC 2406.14927 [abs]; PhysTwin 2503.17973 [abs]; PhysGS 2511.18570 [abs]; gradSim 2104.02646 [abs] | Estimate material/dynamics parameters from video via differentiable simulators or physics-augmented splats/fields; PhysGS does Bayesian inference over per-splat properties; PhysDreamer notes "lack of material ground-truth data"; gradSim calls the problem "fundamentally ill-posed due to the loss of information during image formation" | Same class as elastic/acoustic FWI: forward model + adjoint + misfit. Identifiability, null spaces, experimental design | Estimators are crowded. Less covered: formal identifiability and measurement design (which interaction constrains which parameter) | Strong prior art; no evidence yet for a geophysics-specific gain |
| B1b Differentiable-sim system identification | Interactive Differentiable Simulation 1905.10706; DiffTaichi 1910.00935; Differentiable-sim-based SysID for locomotion 2508.04696; RigPI 2606.25212; Phys2Real 2510.11689 [abs] | Fit simulator parameters by gradients; Phys2Real fuses VLM priors with online adaptation "through uncertainty-aware fusion" | Adjoint/gradient machinery is the same; misfit design and cycle-skipping lessons transfer | Local minima and basin analysis is rarely framed as cycle skipping | Moderate (title-level for most) |
| B1c Real-to-sim-to-real pipelines | RialTo 2403.03949 [abs]; Splatting Physical Scenes 2506.04120 [abs]; D-REX 2603.01151; Robo-GS 2408.14873; SIMPLER 2405.05941 [abs] | Build digital twins from real data and train/evaluate policies; SIMPLER studies "control and visual disparities" between real and sim evaluation | Blind-test and sim/real validation culture; error propagation | The real-to-sim-to-real post reports sim/real rank correlation (A-16); propagating parameter uncertainty to policy outcome was not found in this search across the literature | Moderate |
| B1d Differentiable simulators / engines | MuJoCo Playground 2502.08844; Isaac Lab 2511.04831; DiffTaichi 1910.00935. **NVIDIA Warp and Genesis: software, no paper verified here (UNVERIFIED as references)** | Simulation frameworks for robot learning | HPC/GPU numerics (FD stencils, checkpointing) for wave solvers | No evidence for wave-physics support in these; not checked | Low (not verified) |
| B1e Impact / vibration / tactile sensing | ObjectFolder 2109.07991, 2.0 2204.02389, Benchmark 2306.00956; RealImpact 2306.09944 [abs]; Physics-driven diffusion for impact sound 2303.16897; FillGauss 2607.17773; Taxim 2109.04027 | Multisensory object datasets; real impact-sound recordings (150,000 recordings, 50 objects, "calibration of the sim-to-real gap"); impact-sound generation | Modal and wave-based inversion for stiffness/damping; held-out prediction | Whether these data support calibrated parameter inversion with uncertainty is untested here | Real datasets exist; our beam PoC is synthetic |
| B1f Vibration/modal and impact-echo inspection | Impact-Rover 2208.06305 [abs]; Impact-sounding concrete 2110.13125; Distributed Surface Inspection via Operational Modal Analysis, vibration-sensing swarm 2507.07724 [abs] | Robots collect impact-sounding/impact-echo or vibration data to localise subsurface defects or damage | Wave-based NDE is close to seismic imaging practice (impact-echo ≈ normal-incidence reflection) | Modern migration/FWI-style processing on robot-collected NDE data not surveyed here | Robot NDE exists; gap unproven |
| B1g GPR with robots | CMU-GPR 2107.07606; GPR-assisted robot odometry 2503.18301; GPR terrain classification 2404.09094; GPRNet 2011.02635; 3D metric GPR imaging 2104.10722; bridge-deck NDE robot 1704.04663 | GPR for robot localisation, mapping, utilities reconstruction, metric imaging via dielectric estimation | Dielectric/velocity estimation ≈ migration velocity analysis; GPR imaging is EM seismic-like | Joint visual + geophysical active inspection: not found as a single paper in this search | Components exist; combination unproven |
| B1h Belief-space / active inspection | 3D-Belief 2605.11367 [abs]; belief-free DRL/MCTS for inspection and maintenance 2312.14824 (adjacent only: structural deterioration planning) | World modelling as belief inference with "multi-hypothesis belief sampling" | Experimental design, Bayesian updating, acquisition planning | Searches combining belief-space + subsurface/geophysical sensing: **zero results** (arXiv, this search only) | Gap plausible, unproven |
| B2a Radar/sonar/ultrasound neural rendering | RadarSplat 2506.01379; SonarSplat 2504.00159; NAS-GS 2601.06285; SAR-GS 2506.21633; UltraGS 2511.07743 [abs]; mmIR 2608.28913 [abs]; 3DPS 2609.11894 [abs]; PAGS 2608.25472 [abs] | Gaussian-splat or inverse-rendering models for non-optical wave sensors. 3DPS abstract: optical-NVS ports "discard phase". PAGS: "blind autofocusing PACT via speed-of-sound-adaptive Gaussian splatting" | Phase-aware, coherent modelling and velocity analysis are core seismic skills | Active frontier, becoming crowded. PAGS is the closest to "migration velocity analysis with splats" (full text not read; claim limited to its abstract) | Strong, recent |
| B2b Acoustics for embodied AI | SoundSpaces 1912.11474; SoundSpaces 2.0 2206.08312 [abs]; GWA 2204.01787 [abs]; NAF 2204.00628 [abs]; NACF 2309.15977; AudioGS 2604.08967; neural operators for sound 2308.05141; BatVision 1912.07011; VisualEchoes 2005.01616 | Geometry-based audio rendering on 3D meshes; wave+geometric room impulse response dataset (~2 million IRs, "accurate low-frequency and high-frequency"); implicit acoustic fields | FD/FDTD wave solvers, diffraction, low frequencies | Acoustics on **generated** (not CAD) geometry with propagated geometry uncertainty: not found | Prior art covers rendering; gap narrow |
| B2c NLOS as migration | Lindell et al. 2019, ACM TOG, DOI 10.1145/3306346.3322937; Liu et al. 2019, Nature, DOI 10.1038/s41586-019-1461-3; ToF NLOS study 2603.09548; PlatoNeRF 2312.14239; Transient NeRF 2307.09555 | Migration (f-k) and virtual-wave (phasor field) reconstruction of hidden geometry from transient optical data; multi-bounce lidar for occluded geometry | Direct precedent: **migration-to-3D is established**, not a new claim | Extension to new sensors/regimes only | Strong prior art |
| B3 Geometry evaluation vs task | 2609.06820 [abs]; SIMPLER 2405.05941 [abs]; Habitat 1904.01201; Genie 2402.15391; Cosmos platform 2501.03575; Cosmos 3 2606.02800; World models that know when they don't know 2512.05927 [abs]; Tutorial 2606.12783 | 2609.06820 (active mapping, pretrained occupancy models): "correcting false positives or false negatives alone does not consistently improve final coverage" - "a gap between occupancy accuracy and downstream planning performance". 2512.05927: video world models "often hallucinate"; proposes calibrated uncertainty | Blind-test culture; calibration; QC | Geometry-trust benchmarks tied to robot outcomes: few found | Moderate |
| B4 Sim-ready generation and provenance | HoloScene 2510.05560 [abs]; Infinigen 2306.09310; Infinigen Indoors 2406.11824; REST3D 2605.30338 [abs]; Articulate-Anything 2410.13882; URDFormer 2405.11656; OracleGS 2509.23258 [abs]; 3D-Belief 2605.11367 [abs] | REST3D: "geometrically plausible but physically inconsistent results, including object floating and penetration". OracleGS: MVS "oracle" marks "regions where the generated views are well-supported by multi-view evidence versus ... high uncertainty". 3D-Belief: "represents uncertainty directly in 3D" | Resolution/illumination analysis; posterior sampling; UQ | Generators that track evidence internally exist; post-hoc analysis of the exported splats of a generated world, for a world generated elsewhere, not found | Moderate |

### B5. Where a geophysicist's skills map to an open physical-AI need (honest ledger)

| # | Item | Already covered? (what exists) | What remains open | Evidence level |
|---|---|---|---|---|
| 1 | Illumination / resolution / null-space analysis of generated worlds | **Partly covered**: Fisher/visibility maps in reconstruction (FisherRF 2311.17874, Bayes' Rays 2309.03185, PRIMU 2508.02443), evidence-vs-hallucination inside generators (OracleGS, 3D-Belief), calibrated uncertainty for video world models (2512.05927) | Post-hoc analysis of an exported generated world. Our own PoC: illumination ties plain visibility, so value is in the tiers and the depth-size null space, not the score | Medium (own PoC, synthetic) |
| 2 | Ensembles/posterior sampling of generated worlds | **Partly covered inside generators** (3D-Belief multi-hypothesis sampling; 2512.05927 calibration) | External ensemble test on a commercial model, with shared-error analysis (needs paid credits and permission) | Low (not run) |
| 3 | Wave-physics sensors on generated geometry (acoustic, ultrasound, radar) | **Largely covered for rendering** (SoundSpaces 2.0, GWA, NAF, RadarSplat, SonarSplat, UltraGS, mmIR, 3DPS) | Phase-aware/coherent modelling on generated meshes with geometry-uncertainty propagation; not found | Low-medium; crowded |
| 4 | Hidden-structure inspection by robots (impact-echo, GPR, ultrasound) | **Covered at component level** (Impact-Rover, GPR odometry/GPRNet, OMA swarm) | Joint visual + geophysical active inspection with a proper evaluation; no single paper found | Low-medium |
| 5 | Physical-parameter inversion for real-to-sim | **Heavily covered** (PAC-NeRF, Spring-Gaus, GIC, PhysTwin, gradSim, PhysGS) | Identifiability analysis, measurement/experimental design, model-discrepancy handling | Low-medium |
| 6 | Active tap/impact sensing | **Datasets and generation exist** (ObjectFolder, RealImpact, 2303.16897) | Calibrated stiffness/damping inversion with held-out interactions on real data | Low |
| 7 | Robust misfits (optimal transport) for registration | **Our own PoC**: at its original, smaller compute budget the OT basin was narrower than ICP's; at matched compute the comparison is inconclusive (alignment experiment). Literature on OT misfits for registration was not surveyed in this part | Other OT formulations (image/depth distributions, per-ray 1D) untested | Inconclusive locally |
| 8 | Task-based evaluation of generated geometry | **Partly**: 2609.06820 and SIMPLER show accuracy-vs-task gaps and sim-eval methodology | A trust-map benchmark tied to robot outcomes; our WP1 was inconclusive (underpowered) | Low |
| 9 | Seismic-style large-scale numerics (finite-difference stencils, checkpointing, bricked streaming) | Not verified in the literature by this project; offered only as a general idea, not tied to any company | Unknown | Speculative |
| 10 | Migration / transient imaging transfer | **Established** (Lindell 2019; phasor fields; PlatoNeRF; Transient NeRF) | Only new sensors or regimes; not a novelty claim | Strong prior art |

## Reference list (flat)

Status: **V** = metadata verified this session (arXiv API or Crossref); **V-abs** = abstract also read; **U** = unverified / not a paper.

PhysGaussian 2311.12198 V-abs · PhysDreamer 2404.13026 V-abs · PAC-NeRF 2303.05512 V-abs · Spring-Gaus 2403.09434 V-abs · GIC 2406.14927 V-abs · PhysTwin 2503.17973 V-abs · PhysGS 2511.18570 V-abs · gradSim 2104.02646 V-abs · Interactive Differentiable Simulation 1905.10706 V · DiffTaichi 1910.00935 V · SysID locomotion 2508.04696 V · RigPI 2606.25212 V · Phys2Real 2510.11689 V-abs · RialTo 2403.03949 V-abs · Splatting Physical Scenes 2506.04120 V-abs · D-REX 2603.01151 V · Robo-GS 2408.14873 V · SIMPLER 2405.05941 V-abs · MuJoCo Playground 2502.08844 V · Isaac Lab 2511.04831 V · NVIDIA Warp U · Genesis simulator U · ObjectFolder 2109.07991 V · ObjectFolder 2.0 2204.02389 V · ObjectFolder Benchmark 2306.00956 V · RealImpact 2306.09944 V-abs · Impact-sound diffusion 2303.16897 V · FillGauss 2607.17773 V · Taxim 2109.04027 V · Impact-Rover 2208.06305 V-abs · Impact-sounding concrete 2110.13125 V · OMA swarm 2507.07724 V-abs · CMU-GPR 2107.07606 V · GPR odometry 2503.18301 V · GPR terrain 2404.09094 V · GPRNet 2011.02635 V · 3D metric GPR 2104.10722 V · bridge-deck NDE 1704.04663 V · belief-free DRL inspection 2312.14824 V · 3D-Belief 2605.11367 V-abs · RadarSplat 2506.01379 V · SonarSplat 2504.00159 V · NAS-GS 2601.06285 V · SAR-GS 2506.21633 V · UltraGS 2511.07743 V-abs · mmIR 2608.28913 V-abs · 3DPS mmWave 2609.11894 V-abs · PAGS 2608.25472 V-abs · SoundSpaces 1912.11474 V · SoundSpaces 2.0 2206.08312 V-abs · GWA 2204.01787 V-abs · NAF 2204.00628 V-abs · NACF 2309.15977 V · AudioGS 2604.08967 V · Neural operators sound 2308.05141 V · BatVision 1912.07011 V · VisualEchoes 2005.01616 V · Lindell 2019 DOI 10.1145/3306346.3322937 V · Liu 2019 DOI 10.1038/s41586-019-1461-3 V · ToF NLOS study 2603.09548 V · PlatoNeRF 2312.14239 V · Transient NeRF 2307.09555 V · 2609.06820 V-abs · Habitat 1904.01201 V · Genie 2402.15391 V · Cosmos platform 2501.03575 V · Cosmos 3 2606.02800 V · 2512.05927 V-abs · Tutorial 2606.12783 V · HoloScene 2510.05560 V-abs · Infinigen 2306.09310 V · Infinigen Indoors 2406.11824 V · REST3D 2605.30338 V-abs · Articulate-Anything 2410.13882 V · URDFormer 2405.11656 V · OracleGS 2509.23258 V-abs · FisherRF 2311.17874 V · Bayes' Rays 2309.03185 V · PRIMU 2508.02443 V · FisherRF-nav 2403.11396 V · Meta-IFWI 2604.26938 V · Wave-NTK 2603.22362 V · FM-FWI 2608.05763 V · Diffusion posterior FWI 2512.12797 V · Physical-state-guided FWI 2609.12899 V.

## Website rows

```json
[
{"id":"b1a","topic":"Physical-parameter inversion from video","works":[
 {"title":"PhysGaussian: Physics-Integrated 3D Gaussians for Generative Dynamics","authors":"Xie et al.","year":2023,"id":"2311.12198","verified":true},
 {"title":"PhysDreamer: Physics-Based Interaction with 3D Objects via Video Generation","authors":"Zhang et al.","year":2024,"id":"2404.13026","verified":true},
 {"title":"PAC-NeRF: Physics Augmented Continuum Neural Radiance Fields for Geometry-Agnostic System Identification","authors":"Li et al.","year":2023,"id":"2303.05512","verified":true},
 {"title":"Reconstruction and Simulation of Elastic Objects with Spring-Mass 3D Gaussians","authors":"Zhong et al.","year":2024,"id":"2403.09434","verified":true},
 {"title":"GIC: Gaussian-Informed Continuum for Physical Property Identification and Simulation","authors":"Cai et al.","year":2024,"id":"2406.14927","verified":true},
 {"title":"PhysTwin: Physics-Informed Reconstruction and Simulation of Deformable Objects from Videos","authors":"Jiang et al.","year":2025,"id":"2503.17973","verified":true},
 {"title":"PhysGS: Bayesian-Inferred Gaussian Splatting for Physical Property Estimation","authors":"Chopra et al.","year":2025,"id":"2511.18570","verified":true},
 {"title":"gradSim: Differentiable simulation for system identification and visuomotor control","authors":"Jatavallabhula et al.","year":2021,"id":"2104.02646","verified":true}],
 "relation":"Same inverse-problem class as elastic/acoustic FWI: forward model, adjoint, misfit; identifiability and null spaces apply","gap":"Estimators are crowded; formal identifiability and measurement design are less covered","evidence":"Strong prior art; no geophysics-specific gain shown"},
{"id":"b1b","topic":"Differentiable-simulation system identification","works":[
 {"title":"Interactive Differentiable Simulation","authors":"Heiden et al.","year":2019,"id":"1905.10706","verified":true},
 {"title":"DiffTaichi: Differentiable Programming for Physical Simulation","authors":"Hu et al.","year":2019,"id":"1910.00935","verified":true},
 {"title":"Achieving Precise and Reliable Locomotion with Differentiable Simulation-Based System Identification","authors":"Kovalev et al.","year":2025,"id":"2508.04696","verified":true},
 {"title":"RigPI: Dynamic Parameter Identification of Rigid Body via VLM-Seeded Differentiable Simulation","authors":"He et al.","year":2026,"id":"2606.25212","verified":true},
 {"title":"Phys2Real: Fusing VLM Priors with Interactive Online Adaptation for Uncertainty-Aware Sim-to-Real Manipulation","authors":"Wang et al.","year":2025,"id":"2510.11689","verified":true}],
 "relation":"Adjoint/gradient machinery is identical; cycle-skipping and basin analysis transfer","gap":"Local-minima analysis rarely framed as cycle skipping","evidence":"Moderate (mostly title-level)"},
{"id":"b1c","topic":"Real-to-sim-to-real pipelines and sim evaluation","works":[
 {"title":"Reconciling Reality through Simulation: A Real-to-Sim-to-Real Approach for Robust Manipulation","authors":"Torne et al.","year":2024,"id":"2403.03949","verified":true},
 {"title":"Splatting Physical Scenes: End-to-End Real-to-Sim from Imperfect Robot Data","authors":"Moran et al.","year":2025,"id":"2506.04120","verified":true},
 {"title":"D-REX: Differentiable Real-to-Sim-to-Real Engine for Learning Dexterous Grasping","authors":"Lou et al.","year":2026,"id":"2603.01151","verified":true},
 {"title":"Evaluating Real-World Robot Manipulation Policies in Simulation","authors":"Li et al.","year":2024,"id":"2405.05941","verified":true}],
 "relation":"Blind-test and sim/real validation culture; error propagation","gap":"Propagating parameter uncertainty to policy outcome: not found in this search across the literature","evidence":"Moderate"},
{"id":"b1e","topic":"Impact, vibration and tactile sensing","works":[
 {"title":"ObjectFolder 2.0: A Multisensory Object Dataset for Sim2Real Transfer","authors":"Gao et al.","year":2022,"id":"2204.02389","verified":true},
 {"title":"RealImpact: A Dataset of Impact Sound Fields for Real Objects","authors":"Clarke et al.","year":2023,"id":"2306.09944","verified":true},
 {"title":"Physics-Driven Diffusion Models for Impact Sound Synthesis from Videos","authors":"Su et al.","year":2023,"id":"2303.16897","verified":true},
 {"title":"Taxim: An Example-based Simulation Model for GelSight Tactile Sensors","authors":"Si et al.","year":2021,"id":"2109.04027","verified":true}],
 "relation":"Modal and wave-based inversion for stiffness and damping, with held-out prediction","gap":"Calibrated inversion with uncertainty on real impact data untested here","evidence":"Real datasets exist; our beam PoC is synthetic"},
{"id":"b1f","topic":"Robotic impact-echo, vibration and GPR inspection","works":[
 {"title":"Robotic Inspection and Characterization of Subsurface Defects on Concrete Structures Using Impact Sounding","authors":"Hoxha et al.","year":2022,"id":"2208.06305","verified":true},
 {"title":"Distributed Surface Inspection via Operational Modal Analysis by a Swarm of Miniaturized Vibration-Sensing Robots","authors":"Siemensma et al.","year":2025,"id":"2507.07724","verified":true},
 {"title":"CMU-GPR Dataset: Ground Penetrating Radar Dataset for Robot Localization and Mapping","authors":"Baikovitz et al.","year":2021,"id":"2107.07606","verified":true},
 {"title":"GPR-based Model Reconstruction System for Underground Utilities Using GPRNet","authors":"Feng et al.","year":2020,"id":"2011.02635","verified":true},
 {"title":"Towards 3D Metric GPR Imaging Based on DNN Noise Removal and Dielectric Estimation","authors":"Feng et al.","year":2021,"id":"2104.10722","verified":true}],
 "relation":"Wave-based NDE is close to seismic imaging; dielectric estimation is velocity analysis","gap":"Joint visual plus geophysical active inspection: not found as one paper (arXiv abstract search only)","evidence":"Components exist; combination unproven"},
{"id":"b2a","topic":"Radar, sonar, ultrasound and photoacoustic neural rendering","works":[
 {"title":"RadarSplat: Radar Gaussian Splatting for High-Fidelity Data Synthesis and 3D Reconstruction of Autonomous Driving Scenes","authors":"Kung et al.","year":2025,"id":"2506.01379","verified":true},
 {"title":"SonarSplat: Novel View Synthesis of Imaging Sonar via Gaussian Splatting","authors":"Sethuraman et al.","year":2025,"id":"2504.00159","verified":true},
 {"title":"UltraGS: Real-Time Physically-Decoupled Gaussian Splatting for Ultrasound Novel View Synthesis","authors":"Yang et al.","year":2025,"id":"2511.07743","verified":true},
 {"title":"mmIR: Frequency-Space Inverse Rendering for 3D Millimeter-Wave Radar ADC Synthesis","authors":"Armouti et al.","year":2026,"id":"2608.28913","verified":true},
 {"title":"3D Point Splatting for mmWave Radar Novel View Synthesis","authors":"Armouti et al.","year":2026,"id":"2609.11894","verified":true},
 {"title":"PAGS: Autofocusing Photoacoustic Tomography via Speed-of-Sound-Adaptive Gaussian Splatting","authors":"Ge et al.","year":2026,"id":"2608.25472","verified":true}],
 "relation":"Phase-aware coherent modelling and velocity analysis are core seismic skills","gap":"Active and crowding; PAGS is closest to migration velocity analysis with splats (abstract-level)","evidence":"Strong, recent"},
{"id":"b2b","topic":"Acoustics for embodied AI","works":[
 {"title":"SoundSpaces 2.0: A Simulation Platform for Visual-Acoustic Learning","authors":"Chen et al.","year":2022,"id":"2206.08312","verified":true},
 {"title":"GWA: A Large High-Quality Acoustic Dataset for Audio Processing","authors":"Tang et al.","year":2022,"id":"2204.01787","verified":true},
 {"title":"Learning Neural Acoustic Fields","authors":"Luo et al.","year":2022,"id":"2204.00628","verified":true},
 {"title":"AudioGS: Spectrogram-Based Audio Gaussian Splatting for Sound Field Reconstruction","authors":"Bi et al.","year":2026,"id":"2604.08967","verified":true}],
 "relation":"FD/FDTD wave solvers, diffraction, low-frequency physics","gap":"Wave acoustics on generated (not CAD) geometry with propagated geometry uncertainty: not found","evidence":"Prior art covers rendering; gap narrow"},
{"id":"b2c","topic":"Non-line-of-sight imaging as migration","works":[
 {"title":"Wave-based non-line-of-sight imaging using fast f-k migration","authors":"Lindell et al.","year":2019,"id":"doi:10.1145/3306346.3322937","verified":true},
 {"title":"Non-line-of-sight imaging using phasor-field virtual wave optics","authors":"Liu et al.","year":2019,"id":"doi:10.1038/s41586-019-1461-3","verified":true},
 {"title":"PlatoNeRF: 3D Reconstruction in Plato's Cave via Single-View Two-Bounce Lidar","authors":"Klinghoffer et al.","year":2023,"id":"2312.14239","verified":true},
 {"title":"Transient Neural Radiance Fields for Lidar View Synthesis and 3D Reconstruction","authors":"Malik et al.","year":2023,"id":"2307.09555","verified":true}],
 "relation":"Direct precedent: migration-to-3D is established, not a new claim","gap":"New sensors or regimes only","evidence":"Strong prior art"},
{"id":"b3","topic":"Geometry evaluation against task outcomes, calibrated world models","works":[
 {"title":"Diagnosing and Dynamically Filtering Occupancy World Models for Active Mapping","authors":"Zhang et al.","year":2026,"id":"2609.06820","verified":true},
 {"title":"World Models That Know When They Don't Know - Controllable Video Generation with Calibrated Uncertainty","authors":"Mei et al.","year":2025,"id":"2512.05927","verified":true},
 {"title":"Cosmos World Foundation Model Platform for Physical AI","authors":"NVIDIA et al.","year":2025,"id":"2501.03575","verified":true},
 {"title":"Genie: Generative Interactive Environments","authors":"Bruce et al.","year":2024,"id":"2402.15391","verified":true}],
 "relation":"Blind-test culture, calibration and QC","gap":"Trust-map benchmarks tied to robot outcomes: few found","evidence":"Moderate"},
{"id":"b4","topic":"Sim-ready generation and per-region provenance or uncertainty","works":[
 {"title":"HoloScene: Simulation-Ready Interactive 3D Worlds from a Single Video","authors":"Xia et al.","year":2025,"id":"2510.05560","verified":true},
 {"title":"REST3D: Reconstructing Physically Stable 3D Scenes from a Single Image","authors":"Ma et al.","year":2026,"id":"2605.30338","verified":true},
 {"title":"OracleGS: Grounding Generative Priors for Sparse-View Gaussian Splatting","authors":"Topaloglu et al.","year":2025,"id":"2509.23258","verified":true},
 {"title":"3D-Belief: Embodied Belief Inference via Generative 3D World Modeling","authors":"Yin et al.","year":2026,"id":"2605.11367","verified":true},
 {"title":"Infinite Photorealistic Worlds using Procedural Generation","authors":"Raistrick et al.","year":2023,"id":"2306.09310","verified":true}],
 "relation":"Resolution/illumination analysis, posterior sampling, uncertainty quantification","gap":"Post-hoc analysis of the exported splats of a generated world, for a world generated elsewhere: not found in this search (arXiv search only)","evidence":"Moderate"}
]
```
