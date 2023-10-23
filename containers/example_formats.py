

source_data = {
    "source": "dandi",  # or "s3"
    "source_data_type": "nwb",  # or "spikeglx"
    "source_data_paths": {
        "file": "https://dandiarchive.org/dandiset/000003/0.210813.1807"
    },
    "recording_kwargs": {
        "electrical_series_name": "ElectricalSeries",
    }
}


source_data_2 = {
    "source": "s3",
    "source_data_type": "spikeglx",
    "source_data_paths": {
        "file_bin": "s3://bucket/path/to/file.ap.bin",
        "file_meta": "s3://bucket/path/to/file2.ap.meta",
    },
    "recording_kwargs": {}
}


preprocessing_params = dict(
    preprocessing_strategy="cmr",  # 'destripe' or 'cmr'
    highpass_filter=dict(freq_min=300.0, margin_ms=5.0),
    phase_shift=dict(margin_ms=100.0),
    detect_bad_channels=dict(
        method="coherence+psd",
        dead_channel_threshold=-0.5,
        noisy_channel_threshold=1.0,
        outside_channel_threshold=-0.3,
        n_neighbors=11,
        seed=0,
    ),
    remove_out_channels=False,
    remove_bad_channels=False,
    max_bad_channel_fraction_to_remove=1.1,
    common_reference=dict(reference="global", operator="median"),
    highpass_spatial_filter=dict(
        n_channel_pad=60,
        n_channel_taper=None,
        direction="y",
        apply_agc=True,
        agc_window_length_s=0.01,
        highpass_butter_order=3,
        highpass_butter_wn=0.01,
    ),
)

qm_params = {
    "presence_ratio": {"bin_duration_s": 60},
    "snr": {"peak_sign": "neg", "peak_mode": "extremum", "random_chunk_kwargs_dict": None},
    "isi_violation": {"isi_threshold_ms": 1.5, "min_isi_ms": 0},
    "rp_violation": {"refractory_period_ms": 1, "censored_period_ms": 0.0},
    "sliding_rp_violation": {
        "bin_size_ms": 0.25,
        "window_size_s": 1,
        "exclude_ref_period_below_ms": 0.5,
        "max_ref_period_ms": 10,
        "contamination_values": None,
    },
    "amplitude_cutoff": {
        "peak_sign": "neg",
        "num_histogram_bins": 100,
        "histogram_smoothing_value": 3,
        "amplitudes_bins_min_ratio": 5,
    },
    "amplitude_median": {"peak_sign": "neg"},
    "nearest_neighbor": {"max_spikes": 10000, "min_spikes": 10, "n_neighbors": 4},
    "nn_isolation": {"max_spikes": 10000, "min_spikes": 10, "n_neighbors": 4, "n_components": 10, "radius_um": 100},
    "nn_noise_overlap": {"max_spikes": 10000, "min_spikes": 10, "n_neighbors": 4, "n_components": 10, "radius_um": 100},
}
qm_metric_names = [
    "num_spikes",
    "firing_rate",
    "presence_ratio",
    "snr",
    "isi_violation",
    "rp_violation",
    "sliding_rp_violation",
    "amplitude_cutoff",
    "drift",
    "isolation_distance",
    "l_ratio",
    "d_prime",
]

postprocessing_params = dict(
    sparsity=dict(method="radius", radius_um=100),
    waveforms_deduplicate=dict(
        ms_before=0.5,
        ms_after=1.5,
        max_spikes_per_unit=100,
        return_scaled=False,
        dtype=None,
        precompute_template=("average",),
        use_relative_path=True,
    ),
    waveforms=dict(
        ms_before=3.0,
        ms_after=4.0,
        max_spikes_per_unit=500,
        return_scaled=True,
        dtype=None,
        precompute_template=("average", "std"),
        use_relative_path=True,
    ),
    spike_amplitudes=dict(
        peak_sign="neg",
        return_scaled=True,
        outputs="concatenated",
    ),
    similarity=dict(method="cosine_similarity"),
    correlograms=dict(
        window_ms=100.0,
        bin_ms=2.0,
    ),
    isis=dict(
        window_ms=100.0,
        bin_ms=5.0,
    ),
    locations=dict(method="monopolar_triangulation"),
    template_metrics=dict(upsampling_factor=10, sparsity=None),
    principal_components=dict(n_components=5, mode="by_channel_local", whiten=True),
    quality_metrics=dict(
        qm_params=qm_params, 
        metric_names=qm_metric_names, 
        n_jobs=1
    ),
)

curation_params = dict(
    duplicate_threshold=0.9,
    isi_violations_ratio_threshold=0.5,
    presence_ratio_threshold=0.8,
    amplitude_cutoff_threshold=0.1,
)

visualization_params = dict(
    timeseries=dict(n_snippets_per_segment=2, snippet_duration_s=0.5, skip=False),
    drift=dict(
        detection=dict(method="locally_exclusive", peak_sign="neg", detect_threshold=5, exclude_sweep_ms=0.1),
        localization=dict(ms_before=0.1, ms_after=0.3, local_radius_um=100.0),
        n_skip=30,
        alpha=0.15,
        vmin=-200,
        vmax=0,
        cmap="Greys_r",
        figsize=(10, 10),
    ),
)
