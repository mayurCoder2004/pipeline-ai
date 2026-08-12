import { useState } from 'react';

import {
    Box,
    Autocomplete,
    TextField,
} from '@mui/material';

import { AirtableIntegration } from './integrations/airtable';
import { NotionIntegration } from './integrations/notion';
import { HubSpotIntegration } from './integrations/hubspot';

import { DataForm } from './data-form';


const integrationMapping = {
    Notion: NotionIntegration,
    Airtable: AirtableIntegration,
    HubSpot: HubSpotIntegration,
};


export const IntegrationForm = () => {
    const [integrationParams, setIntegrationParams] = useState({});

    const [user, setUser] = useState('TestUser');

    const [org, setOrg] = useState('TestOrg');

    const [currType, setCurrType] = useState(null);

    const CurrIntegration = integrationMapping[currType];


    const handleIntegrationChange = (event, value) => {
        setCurrType(value);

        // Clear previous integration credentials
        // when switching integrations.
        setIntegrationParams({});
    };


    return (
        <Box
            display="flex"
            justifyContent="center"
            alignItems="center"
            flexDirection="column"
            sx={{
                width: '100%',
            }}
        >

            {/* User / Organization / Integration selection */}

            <Box
                display="flex"
                flexDirection="column"
            >

                <TextField
                    label="User"
                    value={user}
                    onChange={(e) => setUser(e.target.value)}
                    sx={{
                        mt: 2,
                    }}
                />

                <TextField
                    label="Organization"
                    value={org}
                    onChange={(e) => setOrg(e.target.value)}
                    sx={{
                        mt: 2,
                    }}
                />

                <Autocomplete
                    id="integration-type"
                    options={Object.keys(integrationMapping)}
                    value={currType}
                    sx={{
                        width: 300,
                        mt: 2,
                    }}
                    renderInput={(params) => (
                        <TextField
                            {...params}
                            label="Integration Type"
                        />
                    )}
                    onChange={handleIntegrationChange}
                />

            </Box>


            {/* Selected integration */}

            {currType && CurrIntegration && (
                <Box>
                    <CurrIntegration
                        user={user}
                        org={org}
                        integrationParams={integrationParams}
                        setIntegrationParams={
                            setIntegrationParams
                        }
                    />
                </Box>
            )}


            {/* Load data after OAuth */}

            {integrationParams?.credentials && (
                <Box
                    sx={{
                        mt: 2,
                        width: '100%',
                        maxWidth: 600,
                    }}
                >
                    <DataForm
                        integrationType={
                            integrationParams.type
                        }
                        credentials={
                            integrationParams.credentials
                        }
                    />
                </Box>
            )}

        </Box>
    );
};