import React, { useEffect, useState } from 'react';
import '../App.css';

export default function ServiceStatus() {
    const [isLoaded, setIsLoaded] = useState(false);
    const [services, setServices] = useState(null);
    const [error, setError] = useState(null);

    const getHealthStatus = () => {
        fetch(`http://acit3855-lab6a.westus.cloudapp.azure.com/health`)
            .then(res => res.json())
            .then((result) => {
                console.log("Received Health Status")
                setServices(result);
                setIsLoaded(true);
            }, (error) => {
                setError(error);
                setIsLoaded(true);
            })
    }

    useEffect(() => {
        const interval = setInterval(() => getHealthStatus(), 20000); 
        return () => clearInterval(interval);
    }, []);

    if (error) {
        return (<div className={"error"}>Error: {error.message}</div>);
    } else if (!isLoaded) {
        return (<div>Loading...</div>);
    } else {
        return (
            <div>
                <h3>Service Health Status</h3>
                <ul>
                    {Object.entries(services).map(([service, status]) => (
                        <li key={service}>
                            {service}: {status.status} (Last Checked: {status.last_checked})
                        </li>
                    ))}
                </ul>
            </div>
        );
    }
}
