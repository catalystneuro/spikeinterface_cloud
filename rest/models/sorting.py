from pydantic import BaseModel, Field, Extra
from typing import Optional, Dict, List, Union, Tuple
from enum import Enum


# ------------------------------
# Run Models
# ------------------------------
class RunAt(str, Enum):
    aws = "aws"
    local = "local"

class RunKwargs(BaseModel):
    run_at: RunAt = Field(..., description="Where to run the sorting job. Choose from: aws, local.")
    run_identifier: str = Field(..., description="Unique identifier for the run.")
    run_description: str = Field(..., description="Description of the run.")
    test_with_toy_recording: bool = Field(default=False, description="Whether to test with a toy recording.")
    test_with_subrecording: bool = Field(default=False, description="Whether to test with a subrecording.")
    test_subrecording_n_frames: Optional[int] = Field(default=30000, description="Number of frames to use for the subrecording.")
    log_to_file: bool = Field(default=False, description="Whether to log to a file.")


# ------------------------------
# Source Data Models
# ------------------------------
class SourceName(str, Enum):
    s3 = "s3"
    dandi = "dandi"
    local = "local"

class SourceDataType(str, Enum):
    nwb = "nwb"
    spikeglx = "spikeglx"

class SourceDataKwargs(BaseModel):
    source_name: SourceName = Field(..., description="Source of input data. Choose from: s3, dandi, local.")
    source_data_type: SourceDataType = Field(..., description="Type of input data. Choose from: nwb, spikeglx.")
    source_data_paths: Dict[str, str] = Field(..., description="Dictionary with paths to source data. Keys are names of data files, values are urls.")


# ------------------------------
# Output Data Models
# ------------------------------
class OutputDestination(str, Enum):
    s3 = "s3"
    dandi = "dandi"
    local = "local"

class OutputDataKwargs(BaseModel):
    output_destination: OutputDestination = Field(..., description="Destination of output data. Choose from: s3, dandi, local.")
    output_path: str = Field(..., description="Path to output data.")

# ------------------------------
# Recording Models
# ------------------------------
class RecordingKwargs(BaseModel, extra=Extra.allow):
    pass


# ------------------------------
# Preprocessing Models
# ------------------------------
class HighpassFilter(BaseModel):
    freq_min: float = Field(default=300.0, description="Minimum frequency for the highpass filter")
    margin_ms: float = Field(default=5.0, description="Margin in milliseconds")

class PhaseShift(BaseModel):
    margin_ms: float = Field(default=100.0, description="Margin in milliseconds for phase shift")

class DetectBadChannels(BaseModel):
    method: str = Field(default="coherence+psd", description="Method to detect bad channels")
    dead_channel_threshold: float = Field(default=-0.5, description="Threshold for dead channel")
    noisy_channel_threshold: float = Field(default=1.0, description="Threshold for noisy channel")
    outside_channel_threshold: float = Field(default=-0.3, description="Threshold for outside channel")
    n_neighbors: int = Field(default=11, description="Number of neighbors")
    seed: int = Field(default=0, description="Seed value")

class CommonReference(BaseModel):
    reference: str = Field(default="global", description="Type of reference")
    operator: str = Field(default="median", description="Operator used for common reference")

class HighpassSpatialFilter(BaseModel):
    n_channel_pad: int = Field(default=60, description="Number of channels to pad")
    n_channel_taper: Optional[int] = Field(default=None, description="Number of channels to taper")
    direction: str = Field(default="y", description="Direction for the spatial filter")
    apply_agc: bool = Field(default=True, description="Whether to apply automatic gain control")
    agc_window_length_s: float = Field(default=0.01, description="Window length in seconds for AGC")
    highpass_butter_order: int = Field(default=3, description="Order for the Butterworth filter")
    highpass_butter_wn: float = Field(default=0.01, description="Natural frequency for the Butterworth filter")

class PreprocessingKwargs(BaseModel):
    preprocessing_strategy: str = Field(default="cmr", description="Strategy for preprocessing")
    highpass_filter: HighpassFilter
    phase_shift: PhaseShift
    detect_bad_channels: DetectBadChannels
    remove_out_channels: bool = Field(default=False, description="Flag to remove out channels")
    remove_bad_channels: bool = Field(default=False, description="Flag to remove bad channels")
    max_bad_channel_fraction_to_remove: float = Field(default=1.1, description="Maximum fraction of bad channels to remove")
    common_reference: CommonReference
    highpass_spatial_filter: HighpassSpatialFilter


# ------------------------------
# Sorter Models
# ------------------------------
class SorterName(str, Enum):
    ironclust = "ironclust"
    kilosort2 = "kilosort2"
    kilosort25 = "kilosort25"
    kilosort3 = "kilosort3"
    spykingcircus = "spykingcircus"

class SorterKwargs(BaseModel, extra=Extra.allow):
    sorter_name: SorterName = Field(..., description="Name of the sorter to use.")


# ------------------------------
# Postprocessing Models
# ------------------------------
class PresenceRatio(BaseModel):
    bin_duration_s: float = Field(60, description="Duration of the bin in seconds.")

class SNR(BaseModel):
    peak_sign: str = Field("neg", description="Sign of the peak.")
    peak_mode: str = Field("extremum", description="Mode of the peak.")
    random_chunk_kwargs_dict: Optional[dict] = Field(None, description="Random chunk arguments.")

class ISIViolation(BaseModel):
    isi_threshold_ms: float = Field(1.5, description="ISI threshold in milliseconds.")
    min_isi_ms: float = Field(0., description="Minimum ISI in milliseconds.")

class RPViolation(BaseModel):
    refractory_period_ms: float = Field(1., description="Refractory period in milliseconds.")
    censored_period_ms: float = Field(0.0, description="Censored period in milliseconds.")

class SlidingRPViolation(BaseModel):
    min_spikes: int = Field(0, description="Contamination is set to np.nan if the unit has less than this many spikes across all segments.")
    bin_size_ms: float = Field(0.25, description="The size of binning for the autocorrelogram in ms, by default 0.25.")
    window_size_s: float = Field(1, description="Window in seconds to compute correlogram, by default 1.")
    exclude_ref_period_below_ms: float = Field(0.5, description="Refractory periods below this value are excluded, by default 0.5")
    max_ref_period_ms: float = Field(10, description="Maximum refractory period to test in ms, by default 10 ms.")
    contamination_values: Optional[list] = Field(None, description="The contamination values to test, by default np.arange(0.5, 35, 0.5) %")

class PeakSign(str, Enum):
    neg = "neg"
    pos = "pos"
    both = "both"

class AmplitudeCutoff(BaseModel):
    peak_sign: PeakSign = Field("neg", description="The sign of the peaks.")
    num_histogram_bins: int = Field(100, description="The number of bins to use to compute the amplitude histogram.")
    histogram_smoothing_value: int = Field(3, description="Controls the smoothing applied to the amplitude histogram.")
    amplitudes_bins_min_ratio: int = Field(5, description="The minimum ratio between number of amplitudes for a unit and the number of bins. If the ratio is less than this threshold, the amplitude_cutoff for the unit is set to NaN.")

class AmplitudeMedian(BaseModel):
    peak_sign: PeakSign = Field("neg", description="The sign of the peaks.")

class NearestNeighbor(BaseModel):
    max_spikes: int = Field(10000, description="The number of spikes to use, per cluster. Note that the calculation can be very slow when this number is >20000.")
    min_spikes: int = Field(10, description="Minimum number of spikes.")
    n_neighbors: int = Field(4, description="The number of neighbors to use.")

class NNIsolation(NearestNeighbor):
    n_components: int = Field(10, description="The number of PC components to use to project the snippets to.")
    radius_um: int = Field(100, description="The radius, in um, that channels need to be within the peak channel to be included.")

class QMParams(BaseModel):
    presence_ratio: PresenceRatio
    snr: SNR
    isi_violation: ISIViolation
    rp_violation: RPViolation
    sliding_rp_violation: SlidingRPViolation
    amplitude_cutoff: AmplitudeCutoff
    amplitude_median: AmplitudeMedian
    nearest_neighbor: NearestNeighbor
    nn_isolation: NNIsolation
    nn_noise_overlap: NNIsolation

class QualityMetrics(BaseModel):
    qm_params: QMParams = Field(..., description="Quality metric parameters.")
    metric_names: List[str] = Field(..., description="List of metric names to compute.")
    n_jobs: int = Field(1, description="Number of jobs.")

class Sparsity(BaseModel):
    method: str = Field("radius", description="Method for determining sparsity.")
    radius_um: int = Field(100, description="Radius in micrometers for sparsity.")

class Waveforms(BaseModel):
    ms_before: float = Field(3.0, description="Milliseconds before")
    ms_after: float = Field(4.0, description="Milliseconds after")
    max_spikes_per_unit: int = Field(500, description="Maximum spikes per unit")
    return_scaled: bool = Field(True, description="Flag to determine if results should be scaled")
    dtype: Optional[str] = Field(None, description="Data type for the waveforms")
    precompute_template: Tuple[str, str] = Field(("average", "std"), description="Precomputation template method")
    use_relative_path: bool = Field(True, description="Use relative paths")

class SpikeAmplitudes(BaseModel):
    peak_sign: str = Field("neg", description="Sign of the peak")
    return_scaled: bool = Field(True, description="Flag to determine if amplitudes should be scaled")
    outputs: str = Field("concatenated", description="Output format for the spike amplitudes")

class Similarity(BaseModel):
    method: str = Field("cosine_similarity", description="Method to compute similarity")

class Correlograms(BaseModel):
    window_ms: float = Field(100.0, description="Size of the window in milliseconds")
    bin_ms: float = Field(2.0, description="Size of the bin in milliseconds")

class ISIS(BaseModel):
    window_ms: float = Field(100.0, description="Size of the window in milliseconds")
    bin_ms: float = Field(5.0, description="Size of the bin in milliseconds")

class Locations(BaseModel):
    method: str = Field("monopolar_triangulation", description="Method to determine locations")

class TemplateMetrics(BaseModel):
    upsampling_factor: int = Field(10, description="Upsampling factor")
    sparsity: Optional[str] = Field(None, description="Sparsity method")

class PrincipalComponents(BaseModel):
    n_components: int = Field(5, description="Number of principal components")
    mode: str = Field("by_channel_local", description="Mode of principal component analysis")
    whiten: bool = Field(True, description="Whiten the components")

class PostprocessingKwargs(BaseModel):
    sparsity: Sparsity
    waveforms_deduplicate: Waveforms
    waveforms: Waveforms
    spike_amplitudes: SpikeAmplitudes
    similarity: Similarity
    correlograms: Correlograms
    isis: ISIS
    locations: Locations
    template_metrics: TemplateMetrics
    principal_components: PrincipalComponents
    quality_metrics: QualityMetrics

# ------------------------------
# Curation Models
# ------------------------------
class CurationKwargs(BaseModel):
    duplicate_threshold: float = Field(0.9, description="Threshold for duplicate units")
    isi_violations_ratio_threshold: float = Field(0.5, description="Threshold for ISI violations ratio")
    presence_ratio_threshold: float = Field(0.8, description="Threshold for presence ratio")
    amplitude_cutoff_threshold: float = Field(0.1, description="Threshold for amplitude cutoff")


# ------------------------------
# Visualization Models
# ------------------------------
class Timeseries(BaseModel):
    n_snippets_per_segment: int = Field(2, description="Number of snippets per segment")
    snippet_duration_s: float = Field(0.5, description="Duration of the snippet in seconds")
    skip: bool = Field(False, description="Flag to skip")

class Detection(BaseModel):
    method: str = Field("locally_exclusive", description="Method for detection")
    peak_sign: str = Field("neg", description="Sign of the peak")
    detect_threshold: int = Field(5, description="Detection threshold")
    exclude_sweep_ms: float = Field(0.1, description="Exclude sweep in milliseconds")

class Localization(BaseModel):
    ms_before: float = Field(0.1, description="Milliseconds before")
    ms_after: float = Field(0.3, description="Milliseconds after")
    local_radius_um: float = Field(100.0, description="Local radius in micrometers")

class Drift(BaseModel):
    detection: Detection
    localization: Localization
    n_skip: int = Field(30, description="Number of skips")
    alpha: float = Field(0.15, description="Alpha value")
    vmin: int = Field(-200, description="Minimum value")
    vmax: int = Field(0, description="Maximum value")
    cmap: str = Field("Greys_r", description="Colormap")
    figsize: Tuple[int, int] = Field((10, 10), description="Figure size")

class VisualizationKwargs(BaseModel):
    timeseries: Timeseries
    drift: Drift


