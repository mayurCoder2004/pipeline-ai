import { useState } from 'react';

import {
    Box,
    Button,
    Card,
    CardContent,
    Typography,
    Link,
    CircularProgress,
} from '@mui/material';

import axios from 'axios';


const endpointMapping = {
    'Notion': 'notion',
    'Airtable': 'airtable',
    'HubSpot': 'hubspot',
};


export const DataForm = ({ integrationType, credentials }) => {

    const [loadedData, setLoadedData] = useState([]);
    const [isLoading, setIsLoading] = useState(false);


    const endpoint = endpointMapping[integrationType];


    // ============================================================
    // Load data
    // ============================================================

    const handleLoad = async () => {

        try {

            setIsLoading(true);

            const formData = new FormData();

            formData.append(
                'credentials',
                JSON.stringify(credentials)
            );


            const response = await axios.post(
                `http://localhost:8000/integrations/${endpoint}/load`,
                formData
            );


            setLoadedData(response.data || []);

        } catch (e) {

            console.error(e);

            alert(
                e?.response?.data?.detail ||
                'Failed to load data.'
            );

        } finally {

            setIsLoading(false);

        }
    };


    // ============================================================
    // Clear data
    // ============================================================

    const handleClear = () => {

        setLoadedData([]);

    };


    return (

        <Box
            sx={{
                mt: 3,
                width: '100%',
                maxWidth: 700,
            }}
        >

            {/* Header */}

            <Typography
                variant="h6"
                sx={{
                    mb: 2,
                    fontWeight: 600,
                }}
            >
                Loaded {integrationType} Data
            </Typography>


            {/* Buttons */}

            <Box
                display="flex"
                gap={2}
                sx={{ mb: 3 }}
            >

                <Button
                    onClick={handleLoad}
                    variant="contained"
                    disabled={isLoading}
                >

                    {isLoading ? (
                        <>
                            <CircularProgress
                                size={20}
                                sx={{ mr: 1 }}
                            />

                            Loading...
                        </>
                    ) : (
                        'Load Data'
                    )}

                </Button>


                <Button
                    onClick={handleClear}
                    variant="outlined"
                    disabled={
                        isLoading ||
                        loadedData.length === 0
                    }
                >
                    Clear Data
                </Button>

            </Box>


            {/* No data */}

            {loadedData.length === 0 && !isLoading && (

                <Typography
                    variant="body2"
                    color="text.secondary"
                >
                    No data loaded yet. Click "Load Data" to
                    retrieve information from {integrationType}.
                </Typography>

            )}


            {/* Loaded data */}

            <Box
                display="flex"
                flexDirection="column"
                gap={2}
            >

                {loadedData.map((item, index) => (

                    <Card
                        key={item.id || index}
                        variant="outlined"
                    >

                        <CardContent>

                            {/* Name */}

                            <Typography
                                variant="h6"
                                sx={{
                                    fontWeight: 600,
                                    mb: 1,
                                }}
                            >
                                {item.name || 'Unnamed Item'}
                            </Typography>


                            {/* Type */}

                            <Typography
                                variant="body2"
                                color="text.secondary"
                                sx={{ mb: 0.5 }}
                            >
                                <strong>Type:</strong>{' '}
                                {item.type || 'Unknown'}
                            </Typography>


                            {/* ID */}

                            <Typography
                                variant="body2"
                                color="text.secondary"
                                sx={{ mb: 0.5 }}
                            >
                                <strong>ID:</strong>{' '}
                                {item.id || 'N/A'}
                            </Typography>


                            {/* Created */}

                            {item.creation_time && (

                                <Typography
                                    variant="body2"
                                    color="text.secondary"
                                    sx={{ mb: 0.5 }}
                                >
                                    <strong>Created:</strong>{' '}
                                    {new Date(
                                        item.creation_time
                                    ).toLocaleString()}
                                </Typography>

                            )}


                            {/* Modified */}

                            {item.last_modified_time && (

                                <Typography
                                    variant="body2"
                                    color="text.secondary"
                                    sx={{ mb: 1 }}
                                >
                                    <strong>Last Modified:</strong>{' '}
                                    {new Date(
                                        item.last_modified_time
                                    ).toLocaleString()}
                                </Typography>

                            )}


                            {/* URL */}

                            {item.url && (

                                <Link
                                    href={item.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    underline="hover"
                                >
                                    Open in {integrationType}
                                </Link>

                            )}

                        </CardContent>

                    </Card>

                ))}

            </Box>

        </Box>

    );
};