export interface SorterSchema {
    [key: string]: {
        type: string;
        default: any;
        description: string;
        [key: string]: any; // allow for additional properties
    };
}

export const kilosort2_5: SorterSchema = {
    detect_threshold: {
        type: 'float',
        default: 6,
        description: 'Threshold for spike detection',
    },
    projection_threshold: {
        type: 'array',
        default: [10, 4],
        description: 'Threshold on projections',
    },
    preclust_threshold: {
        type: 'float',
        default: 8,
        description: 'Threshold crossings for pre-clustering (in PCA projection space)',
    },
    car: {
        type: 'boolean',
        default: true,
        description: 'Enable or disable common reference',
    },
    minFR: {
        type: 'float',
        default: 0.1,
        description: 'Minimum spike rate [Hz], if a cluster falls below this for too long it gets removed',
    },
    minfr_goodchannels: {
        type: 'float',
        default: 0.1,
        description: 'Minimum firing rate on a good channel [Hz]',
    },
    nblocks: {
        type: 'integer',
        default: 5,
        description: 'Blocks for registration. 0 turns it off, 1 does rigid registration',
    },
    sig: {
        type: 'float',
        default: 20,
        description: 'Spatial smoothness constant for registration',
    },
    freq_min: {
        type: 'float',
        default: 150,
        description: 'High-pass filter cutoff frequency (Hz)',
    },
    sigmaMask: {
        type: 'float',
        default: 30,
        description: 'Spatial constant in um for computing residual variance of spike',
    },
    nPCs: {
        type: 'integer',
        default: 3,
        description: 'Number of PCA dimensions',
    },
    ntbuff: {
        type: 'integer',
        default: 64,
        description: 'Samples of symmetrical buffer for whitening and spike detection',
    },
    nfilt_factor: {
        type: 'integer',
        default: 4,
        description: 'Max number of clusters per good channel (even temporary ones) 4',
    },
    do_correction: {
        type: 'boolean',
        default: true,
        description: 'If True drift registration is applied',
    },
    NT: {
        type: 'integer',
        default: null,
        description: 'Batch size (if None it is automatically computed)',
    },
    keep_good_only: {
        type: 'boolean',
        default: false,
        description: 'If True only good units are returned',
    },
    wave_length: {
        type: 'integer',
        default: 61,
        description: 'size of the waveform extracted around each detected peak, (Default 61, maximum 81)',
    },
    n_jobs: {
        type: 'integer',
        default: -1,
        description: 'Number of jobs (when saving ti binary) - default -1 (all cores)',
    },
    chunk_duration: {
        type: 'string',
        default: '1s',
        description: 'Chunk duration as float with units (e.g. 1s, 500ms) (when saving to binary)',
    }
};

export const kilosort3: SorterSchema = {
    detect_threshold: {
        type: 'float',
        default: 6,
        description: 'Threshold for spike detection',
    },
    projection_threshold: {
        type: 'array',
        default: [9, 9],
        description: 'Threshold on projections',
    },
    preclust_threshold: {
        type: 'float',
        default: 8,
        description: 'Threshold crossings for pre-clustering (in PCA projection space)',
    },
    car: {
        type: 'boolean',
        default: true,
        description: 'Enable or disable common reference',
    },
    minFR: {
        type: 'float',
        default: 0.2,
        description: 'Minimum spike rate [Hz], if a cluster falls below this for too long it gets removed',
    },
    minfr_goodchannels: {
        type: 'float',
        default: 0.2,
        description: 'Minimum firing rate on a good channel [Hz]',
    },
    nblocks: {
        type: 'integer',
        default: 5,
        description: 'Blocks for registration. 0 turns it off, 1 does rigid registration',
    },
    sig: {
        type: 'float',
        default: 20,
        description: 'Spatial smoothness constant for registration',
    },
    freq_min: {
        type: 'float',
        default: 300,
        description: 'High-pass filter cutoff frequency (Hz)',
    },
    sigmaMask: {
        type: 'float',
        default: 30,
        description: 'Spatial constant in um for computing residual variance of spike',
    },
    nPCs: {
        type: 'integer',
        default: 3,
        description: 'Number of PCA dimensions',
    },
    ntbuff: {
        type: 'integer',
        default: 64,
        description: 'Samples of symmetrical buffer for whitening and spike detection',
    },
    nfilt_factor: {
        type: 'integer',
        default: 4,
        description: 'Max number of clusters per good channel (even temporary ones) 4',
    },
    do_correction: {
        type: 'boolean',
        default: true,
        description: 'If True drift registration is applied',
    },
    NT: {
        type: 'integer',
        default: null,
        description: 'Batch size (if None it is automatically computed)',
    },
    keep_good_only: {
        type: 'boolean',
        default: false,
        description: 'If True only good units are returned',
    },
    wave_length: {
        type: 'integer',
        default: 61,
        description: 'size of the waveform extracted around each detected peak, (Default 61, maximum 81)',
    },
    n_jobs: {
        type: 'integer',
        default: -1,
        description: 'Number of jobs (when saving ti binary) - default -1 (all cores)',
    },
    chunk_duration: {
        type: 'string',
        default: '1s',
        description: 'Chunk duration as float with units (e.g. 1s, 500ms) (when saving to binary)',
    }
};

