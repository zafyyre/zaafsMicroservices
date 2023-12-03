import React from 'react';
import logo from './logo.png';
import './App.css';

import EndpointAudit from './components/EndpointAudit';
import AppStats from './components/AppStats';
import ServiceStatus from './components/ServiceStatus'; // Import the new component

function App() {
    const endpoints = ["teams", "players"];

    const rendered_endpoints = endpoints.map((endpoint) => {
        return <EndpointAudit key={endpoint} endpoint={endpoint}/>;
    });

    return (
        <div className="App">
            <img src={logo} className="App-logo" alt="logo" height="150px" width="400px"/>
            <div>
                <AppStats/>
                <h1>Audit Endpoints</h1>
                {rendered_endpoints}
                <h1>Service Health Status</h1> {/* Add a title for the new section */}
                <ServiceStatus/> {/* Include the new ServiceStatus component */}
            </div>
        </div>
    );
}

export default App;
