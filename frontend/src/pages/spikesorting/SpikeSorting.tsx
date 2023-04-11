import React, { useState, useEffect } from 'react';
import {
    Box,
    FormControl,
    InputLabel,
    MenuItem,
    Select,
    TextField,
    Typography,
    Button,
    Switch,
    FormControlLabel,
    SelectChangeEvent,
    Tooltip,
    IconButton,
    Accordion,
    AccordionSummary,
    LinearProgress,
    Snackbar,
    Alert,
    AlertColor
} from '@mui/material';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import Markdown from 'markdown-to-jsx';
import axios from 'axios';

import './SpikeSorting.css';
import { SorterSchema, kilosort2_5, kilosort3 } from './sorterSchemas';
import { restApiClient } from '../../services/clients/restapi.client';



const itemSchemas: { [itemName: string]: SorterSchema } = {
    'Kilosort2_5': kilosort2_5,
    'Kilosort3': kilosort3,
};

interface SpikeSortingProps {
    dandisets_labels: string[];
}

interface FormValues {
    [key: string]: any;
}


const SpikeSorting: React.FC<SpikeSortingProps> = ({ dandisets_labels }) => {
    const [description, setDescription] = useState<string>('');
    const [source, setSource] = useState<string>('DANDI');
    const [sourceDataType, setSourceDataType] = useState<string>('');
    const [sourceDataUrls, setSourceDataUrls] = useState<string[]>([]);
    const [selectedDandiset, setSelectedDandiset] = useState<string>('');
    const [selectedDandisetMetadata, setSelectedDandisetMetadata] = useState<{
        name?: string;
        url?: string;
        description?: string;
    }>({});
    const [listOfFiles, setListOfFiles] = useState<string[]>([]);
    const [selectedDandiFile, setSelectedDandiFile] = useState<string>('');
    const [selectedDandiFileInfo, setSelectedDandiFileInfo] = useState<{
        url?: string;
        acquisition?: { [key: string]: {} }
    }>({});
    const [listOfES, setListOfES] = useState<string[]>([]);
    const [selectedAcquisition, setSelectedAcquisition] = useState<string>('');
    const [selectedAcquisitionMetadata, setSelectedAcquisitionMetadata] = useState<{
        name?: string;
        description?: string;
        rate?: number;
        unit?: string;
        duration?: number;
        n_traces?: number;
    }>({});
    const [processing, setProcessing] = useState<string[]>([]);
    const [subformsProcessing, setSubformsProcessing] = useState<React.ReactNode[]>([]);
    const [sorters, setSorters] = useState<string[]>([]);
    const [subformsSorters, setSubformsSorters] = useState<React.ReactNode[]>([]);
    const [formDataSorters, setFormDataSorters] = useState<FormValues>({});
    const [outputDestination, setOutputDestination] = useState<string>('S3');
    const [outputPath, setOutputPath] = useState<string>('');

    const [loadingDataset, setLoadingDataset] = useState(false)
    const [loadingFile, setLoadingFile] = useState(false)
    const [snackbarOpen, setSnackbarOpen] = useState(false);
    const [snackbarMessage, setSnackbarMessage] = useState('');
    const [snackbarSeverity, setSnackbarSeverity] = useState<AlertColor | undefined>(undefined);

    const handleSnackbarClose = () => setSnackbarOpen(false);

    // Description
    const handleDescriptionChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const desc = event.target.value as string;
        setDescription(desc);
    };

    // Change Data Source
    const handleSourceChange = (event: SelectChangeEvent<string>) => {
        setSource(event.target.value as string);
    };

    // Change Source Data Type
    const handleSourceDataTypeChange = (event: SelectChangeEvent<string>) => {
        setSourceDataType(event.target.value as string);
    };

    // Selected Dandiset
    const handleDandisetChange = async (event: SelectChangeEvent<string>) => {
        const dandiset = event.target.value as string;
        setSelectedDandiset(event.target.value);

        // Extract the id from the selected DANDIset string
        const dandiset_id = dandiset.split(' - ')[0];

        setLoadingDataset(true);

        // Fetch metadata
        try {
            // const response = await axios.get('http://localhost:5000/api/dandi/get-dandiset-metadata', { params: { dandiset_id } });
            const response = await restApiClient.get(
                '/dandi/get-dandiset-metadata',
                { params: { dandiset_id } }
            );
            setSelectedDandisetMetadata(response.data.metadata);
            setListOfFiles(response.data.list_of_files);
        } catch (error) {
            console.error('Error fetching DANDIset metadata:', error);
        } finally {
            setLoadingDataset(false);
        }
    };

    // Selected File
    const handleFileChange = async (event: SelectChangeEvent<string>) => {
        setSelectedDandiFile(event.target.value);
        const filepath = event.target.value as string;

        // Extract the id from the selected DANDIset string
        const dandiset_id = selectedDandiset.split(' - ')[0];

        setLoadingFile(true);
        setSelectedAcquisition('');
        setSelectedAcquisitionMetadata({});

        // Fetch file metadata
        try {
            const response = await axios.get('http://localhost:8000/api/dandi/get-nwbfile-info',
                {
                    params: {
                        dandiset_id: dandiset_id,
                        file_path: filepath
                    }
                }
            );
            const ESNames = Object.keys(response.data.file_info.acquisition);
            setListOfES(ESNames)
            setSelectedDandiFileInfo(response.data.file_info);
        } catch (error) {
            console.error('Error fetching DANDIset metadata:', error);
        } finally {
            // Set loading state to false
            setLoadingFile(false);
        }
    };

    // Selected Acquisition name
    const handleAcquisitionChange = async (event: SelectChangeEvent<string>) => {
        setSelectedAcquisition(event.target.value);
        const acq = event.target.value as string;

        // Show Acquisition metadata
        try {
            const acqMetadata = selectedDandiFileInfo.acquisition?.[acq] || {};
            setSelectedAcquisitionMetadata(acqMetadata);
        } catch (error) {
            console.error('Error changing Acquisition:', error);
        } finally { }
    };

    // Change Sorter items
    const handleSorterChange = (event: SelectChangeEvent<string[]>) => {
        const selectedSorters = event.target.value as string[];
        setSorters(selectedSorters);
        updateSorterSubforms(selectedSorters);
    };

    const updateSorterSubforms = (selectedItems: string[]) => {
        const newSubforms = selectedItems.map((selectedItem) => {
            const schema = itemSchemas[selectedItem];

            return (
                <Accordion key={selectedItem}>
                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                        <Typography>{selectedItem} parameters</Typography>
                    </AccordionSummary>
                    <Box key={selectedItem}>
                        {Object.entries(schema).map(([key, field]) => (
                            <Box className="formItem formItemCompact" key={`${selectedItem}-${key}`}>
                                <Typography className="label">{key}:</Typography>
                                {field.type === 'boolean' ? (
                                    <FormControlLabel
                                        className="compactSwitch"
                                        control={
                                            <Switch
                                                defaultChecked={field.default}
                                                onChange={e => handleInputChange(selectedItem, key, e.target.checked)}
                                            />
                                        }
                                        label=""
                                    />
                                ) : (
                                    <TextField
                                        className={`formControl compactTextField`}
                                        type={field.type === 'float' ? 'number' : field.type}
                                        inputProps={field.type === 'int' ? { step: 1 } : undefined}
                                        defaultValue={field.default}
                                        onChange={e => handleInputChange(selectedItem, key, e.target.value)}
                                    />
                                )}
                                <Tooltip title={field.description} arrow>
                                    <IconButton size="small" color="primary">
                                        <HelpOutlineIcon fontSize="small" />
                                    </IconButton>
                                </Tooltip>
                            </Box>
                        ))}
                    </Box>
                </Accordion>
            );
        });

        setSubformsSorters(newSubforms);
    };

    // Whenever the selection of sorters changes, update the store of subforms data
    useEffect(() => {
        // Find the schema names that are new or removed
        const newSchemaNames = sorters.filter(schemaName => !formDataSorters[schemaName]);
        const removedSchemaNames = Object.keys(formDataSorters).filter(schemaName => !sorters.includes(schemaName));

        // Copy the existing formDataSorters
        const updatedFormDataSorters = { ...formDataSorters };

        // Remove the data for removed schema names
        removedSchemaNames.forEach(schemaName => {
            delete updatedFormDataSorters[schemaName];
        });

        // Add the default data for new schema names
        newSchemaNames.forEach(schemaName => {
            const schema = itemSchemas[schemaName];
            updatedFormDataSorters[schemaName] = {};
            Object.entries(schema).forEach(([key, field]) => {
                updatedFormDataSorters[schemaName][key] = field.default;
            });
        });

        setFormDataSorters(updatedFormDataSorters);
    }, [sorters]);

    // Whenerver the form data changes, update the store of subforms data
    const handleInputChange = (subformName: string, key: string, value: boolean | number | string) => {
        setFormDataSorters((prevData: { [key: string]: SorterSchema }) => {
            const subformData = prevData[subformName];
            const updatedSchemaData = {
                ...subformData,
                [key]: value
            };
            const updatedFormDataSorters = {
                ...prevData,
                [subformName]: updatedSchemaData
            };
            return updatedFormDataSorters;
        });
    };


    // Change Preprocessing items
    const handleProcessingChange = (event: SelectChangeEvent<string[]>) => {
        const selectedItems = event.target.value as string[];
        setProcessing(selectedItems);
        updateProcessingSubforms(selectedItems);
    };

    const updateProcessingSubforms = (selectedSorters: string[]) => {
        const newSubforms = selectedSorters.map((selectedItems) => {
            console.log(selectedItems);
            // const schema = {
            //     'Item 1': kilosort2_5,
            //     'Item 2': kilosort3,
            // }[selectedItems] as SorterSchema;

            //     return (
            //         <Box key={selectedItems}>
            //             <Typography>{selectedItems} Options</Typography>
            //             {Object.entries(schema).map(([key, type]) => (
            //                 <Box className="formItem" key={`${selectedItems}-${key}`}>
            //                     <Typography className="label">{key}:</Typography>
            //                     <TextField
            //                         className="formControl"
            //                         type={type === 'float' ? 'number' : type}
            //                         inputProps={type === 'int' ? { step: 1 } : undefined}
            //                         defaultValue={type === 'boolean' ? false : ''}
            //                     />
            //                 </Box>
            //             ))}
            //         </Box>
            //     );
            // });

            // setSubformsProcessing(newSubforms);
        });
    };

    // Output controls
    const handleOutputDestinationChange = (event: SelectChangeEvent<string>) => {
        const selectedOutput = event.target.value as string;
        setOutputDestination(selectedOutput);
    };

    const handleOutputPathChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const selectedOutputPath = event.target.value as string;
        setOutputPath(selectedOutputPath);
    };

    // Run sorting job
    const handleRunSortingJob = async (runAt: "local" | "aws") => {
        const dandiset_id = selectedDandiset.split(' - ')[0];
        const es = selectedAcquisition as string;

        let target_output_type: string;
        if (runAt === "aws") {
            target_output_type = "s3";
        } else {
            target_output_type = "local";
        }

        const data = {
            run_at: runAt,
            run_identifier: null,
            run_description: description,
            source: source.toLowerCase(),
            source_data_type: sourceDataType.toLowerCase(),
            source_data_urls: sourceDataUrls,
            recording_kwargs: {},
            target_output_type: target_output_type,
            output_path: outputPath,
            sorters_names_list: sorters,
            sorters_kwargs: formDataSorters,
            test_with_toy_recording: false,
            test_with_subrecording: false,
            test_subrecording_n_frames: 30000,
            log_to_file: true,
        };
        try {
            const response = await restApiClient.post('/sorting/run', data);
            setSnackbarMessage(response.data.message + '\nRun identifier: ' + response.data.run_identifier);
            setSnackbarSeverity('success');
        } catch (error: unknown) {
            setSnackbarMessage((error as Error).message);
            setSnackbarSeverity('error');
            console.error(error);
        }
        setSnackbarOpen(true);
    }

    return (
        <Box className="container">
            <Box className="form">
                <Box className="formItem">
                    <FormControl fullWidth>
                        <TextField label="Description" onChange={handleDescriptionChange} />
                    </FormControl>
                </Box>
            </Box>

            <Box component="form" className="form">
                <Typography gutterBottom className="heading" style={{ fontSize: 28, marginTop: '-20px' }}>
                    Data source
                </Typography>
                <Box className="formItem">
                    <FormControl className="formControl_1">
                        <InputLabel>Source</InputLabel>
                        <Select value={source} onChange={handleSourceChange}>
                            <MenuItem value="DANDI">DANDI</MenuItem>
                            <MenuItem value="S3">S3</MenuItem>
                            <MenuItem disabled value="Dataset">Dataset</MenuItem>
                            <MenuItem disabled value="Local">Local</MenuItem>
                        </Select>
                    </FormControl>
                    {source === 'DANDI' ? (
                        <FormControl className="formControl_2">
                            <InputLabel>Choose DANDIset</InputLabel>
                            <Select
                                value={selectedDandiset}
                                onChange={handleDandisetChange}
                                MenuProps={{
                                    PaperProps: {
                                        style: {
                                            maxHeight: 48 * 10, // 48px is the height of each MenuItem
                                            width: 'fit-content',
                                        },
                                    },
                                }}
                            >
                                {dandisets_labels.map((dandiset) => (
                                    <MenuItem key={dandiset} value={dandiset} className="menuItem">
                                        {dandiset}
                                    </MenuItem>
                                ))}
                            </Select>
                        </FormControl>
                    ) : (
                        <FormControl className="formControl_1">
                            <InputLabel>Data type</InputLabel>
                            <Select value={sourceDataType} onChange={handleSourceDataTypeChange}>
                                <MenuItem value="NWB">NWB</MenuItem>
                                <MenuItem value="SpikeGLX">SpikeGLX</MenuItem>
                            </Select>
                        </FormControl>
                    )}
                </Box>

                {source === 'DANDI' ? (
                    <div>
                        {loadingDataset ? <LinearProgress sx={{ marginBottom: 2 }} /> : null}
                        {selectedDandisetMetadata.description && (
                            <Box mt={2} className="MarkdownSummary">
                                <Markdown>
                                    {`**${selectedDandisetMetadata.name}**\n
${selectedDandisetMetadata.url}\n\n
${selectedDandisetMetadata.description}`}
                                </Markdown>
                            </Box>
                        )}

                        <Box className="formItem">
                            <Typography sx={{ marginRight: 2 }}>Select File:</Typography>
                            <FormControl fullWidth>
                                <InputLabel>File</InputLabel>
                                <Select
                                    value={selectedDandiFile}
                                    onChange={handleFileChange}
                                    MenuProps={{
                                        PaperProps: {
                                            style: {
                                                maxHeight: 48 * 10, // 48px is the height of each MenuItem
                                                width: 'fit-content',
                                            },
                                        },
                                    }}
                                >
                                    {listOfFiles.map((file) => (
                                        <MenuItem key={file} value={file}>
                                            {file}
                                        </MenuItem>
                                    ))}
                                </Select>
                            </FormControl>
                        </Box>
                        {loadingFile ? <LinearProgress sx={{ marginBottom: 2 }} /> : null}
                        <Box className="formItem">
                            <FormControl sx={{ width: '50%', marginRight: 1 }}>
                                <InputLabel>Acquisition name</InputLabel>
                                <Select
                                    value={selectedAcquisition}
                                    onChange={handleAcquisitionChange}
                                    MenuProps={{
                                        PaperProps: {
                                            style: {
                                                maxHeight: 48 * 10, // 48px is the height of each MenuItem
                                                width: 'fit-content',
                                            },
                                        },
                                    }}
                                >
                                    {listOfES.map((es) => (
                                        <MenuItem key={es} value={es}>
                                            {es}
                                        </MenuItem>
                                    ))}
                                </Select>
                            </FormControl>

                            {selectedDandiFileInfo && (
                                <Box mt={2} className="MarkdownSummary">
                                    <Markdown>
                                        {`${selectedAcquisitionMetadata.description}\n
**Duration:** ${selectedAcquisitionMetadata.duration} seconds\n
**Number of traces:** ${selectedAcquisitionMetadata.n_traces}\n
**Sampling rate:** ${selectedAcquisitionMetadata.rate} Hz\n
**Unit:** ${selectedAcquisitionMetadata.unit}\n`}
                                    </Markdown>
                                </Box>
                            )}
                        </Box>
                    </div>
                ) : source === 'S3' && sourceDataType === 'NWB' ? (
                    <div>
                        <Box className="formItem">
                            <Typography sx={{ marginRight: 2 }}>S3 path:</Typography>
                            <TextField fullWidth label="s3://bucket/path_to/file.nwb" />
                        </Box>
                        <Box className="formItem">
                            <Typography sx={{ marginRight: 2 }}>Acquisition name:</Typography>
                            <TextField fullWidth label="Acquisition name" />
                        </Box>
                    </div>
                ) : source === 'S3' && sourceDataType === 'SpikeGLX' ? (
                    <div>
                        <Box className="formItem">
                            <Typography sx={{ marginRight: 2 }}>S3 path bin:</Typography>
                            <TextField fullWidth label="s3://bucket/path_to/file.ap.bin" />
                        </Box>
                        <Box className="formItem">
                            <Typography sx={{ marginRight: 2 }}>S3 path meta:</Typography>
                            <TextField fullWidth label="s3://bucket/path_to/file.ap.meta" />
                        </Box>
                    </div>
                ) : null}

            </Box>

            <Box component="form" className="form">
                <Typography gutterBottom className="heading" style={{ fontSize: 28, marginTop: '-20px' }}>
                    Pre-processing
                </Typography>
                <Box className="formItem">
                    <Typography sx={{ marginRight: 2 }}>Pre-processing:</Typography>
                    <FormControl fullWidth disabled>
                        <InputLabel>Pre-processing</InputLabel>
                        <Select<string[]> multiple value={processing} onChange={handleProcessingChange}>
                            <MenuItem value="Item 1">Item 1</MenuItem>
                            <MenuItem value="Item 2">Item 2</MenuItem>
                        </Select>
                    </FormControl>
                </Box>
                {subformsProcessing}
            </Box>

            <Box component="form" className="form">
                <Typography gutterBottom className="heading" style={{ fontSize: 28, marginTop: '-20px' }}>
                    Spike Sorting
                </Typography>
                <Box className="formItem">
                    <Typography sx={{ marginRight: 2 }}>Choose sorters:</Typography>
                    <FormControl fullWidth>
                        <InputLabel>Sorters</InputLabel>
                        <Select<string[]> multiple value={sorters} onChange={handleSorterChange}>
                            <MenuItem value="Kilosort2_5">Kilosort2_5</MenuItem>
                            <MenuItem value="Kilosort3">Kilosort3</MenuItem>
                        </Select>
                    </FormControl>
                </Box>
                {subformsSorters}
            </Box>

            <Box component="form" className="form">
                <Typography gutterBottom className="heading" style={{ fontSize: 28, marginTop: '-20px' }}>
                    Output
                </Typography>
                <Box className="formItem">
                    <FormControl className="formControl_1">
                        <InputLabel>Destination</InputLabel>
                        <Select value={outputDestination} onChange={handleOutputDestinationChange}>
                            <MenuItem value="S3">S3</MenuItem>
                            <MenuItem disabled value="DANDI">DANDI</MenuItem>
                            <MenuItem disabled value="Local">Local</MenuItem>
                        </Select>
                    </FormControl>
                    <TextField fullWidth label="Path" onChange={handleOutputPathChange} />
                </Box>
            </Box>

            <Box component="form">
                <Button
                    variant="contained"
                    color="primary"
                    className="button"
                    style={{ marginRight: "1rem" }}
                    onClick={() => handleRunSortingJob('local')}
                >
                    Run local
                </Button>
                <Button
                    variant="contained"
                    color="primary"
                    className="button"
                    style={{ marginRight: "1rem" }}
                    onClick={() => handleRunSortingJob('aws')}
                >
                    Run AWS
                </Button>
                <Button disabled variant="contained" color="primary" className="button">
                    Save Template
                </Button>
            </Box>

            <Snackbar open={snackbarOpen} autoHideDuration={10000} onClose={handleSnackbarClose} anchorOrigin={{ vertical: 'top', horizontal: 'right' }}>
                <Alert
                    onClose={handleSnackbarClose}
                    severity={snackbarSeverity}
                    sx={{ width: '100%', border: '1px solid green;', borderRadius: "3px" }}
                >
                    {snackbarMessage}
                </Alert>
            </Snackbar>

            <div style={{ height: '50px' }} />

        </Box>
    );
};
export default SpikeSorting;
