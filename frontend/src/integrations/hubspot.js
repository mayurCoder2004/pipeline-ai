import { useEffect, useState } from 'react';
import {
    Box,
    Button,
    CircularProgress,
} from '@mui/material';
import axios from 'axios';

export const HubSpotIntegration = ({
    user,
    org,
    integrationParams,
    setIntegrationParams,
}) => {
    const [isConnected, setIsConnected] = useState(false);
    const [isConnecting, setIsConnecting] = useState(false);

    const handleConnectClick = async () => {
        try {
            setIsConnecting(true);

            const formData = new FormData();
            formData.append('user_id', user);
            formData.append('org_id', org);

            const response = await axios.post(
                'http://localhost:8000/integrations/hubspot/authorize',
                formData
            );

            const authURL = response?.data;

            if (!authURL) {
                throw new Error('HubSpot authorization URL was not returned.');
            }

            const newWindow = window.open(
                authURL,
                'HubSpot Authorization',
                'width=600,height=600'
            );

            if (!newWindow) {
                setIsConnecting(false);
                alert(
                    'Unable to open the HubSpot authorization window. Please allow popups for localhost.'
                );
                return;
            }

            const pollTimer = window.setInterval(() => {
                if (newWindow.closed) {
                    window.clearInterval(pollTimer);
                    handleWindowClosed();
                }
            }, 500);

        } catch (e) {
            setIsConnecting(false);

            alert(
                e?.response?.data?.detail ||
                e?.message ||
                'Failed to connect to HubSpot.'
            );
        }
    };

    const handleWindowClosed = async () => {
        try {
            const formData = new FormData();
            formData.append('user_id', user);
            formData.append('org_id', org);

            const response = await axios.post(
                'http://localhost:8000/integrations/hubspot/credentials',
                formData
            );

            const credentials = response.data;

            if (!credentials) {
                throw new Error('No HubSpot credentials were returned.');
            }

            setIsConnected(true);

            setIntegrationParams((prev) => ({
                ...prev,
                credentials,
                type: 'HubSpot',
            }));

        } catch (e) {
            alert(
                e?.response?.data?.detail ||
                e?.message ||
                'Failed to retrieve HubSpot credentials.'
            );
        } finally {
            setIsConnecting(false);
        }
    };

    useEffect(() => {
        setIsConnected(
            Boolean(integrationParams?.credentials)
        );
    }, [integrationParams]);

    return (
        <Box sx={{ mt: 2 }}>
            <Box
                display="flex"
                alignItems="center"
                justifyContent="center"
                sx={{ mt: 2 }}
            >
                <Button
                    variant="contained"
                    onClick={
                        isConnected
                            ? undefined
                            : handleConnectClick
                    }
                    color={
                        isConnected
                            ? 'success'
                            : 'primary'
                    }
                    disabled={isConnecting || isConnected}
                    sx={{
                        minWidth: 220,
                    }}
                >
                    {isConnected ? (
                        'HubSpot Connected'
                    ) : isConnecting ? (
                        <CircularProgress
                            size={20}
                            color="inherit"
                        />
                    ) : (
                        'Connect to HubSpot'
                    )}
                </Button>
            </Box>
        </Box>
    );
};