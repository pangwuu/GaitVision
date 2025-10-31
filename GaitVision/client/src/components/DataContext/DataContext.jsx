import { createContext, useState, useContext, useEffect } from 'react';

const DataContext = createContext(null);

export function DataProvider({ children }) {
    const [csvData, setCsvData] = useState(null);
    const [selectedMetrics, setSelectedMetrics] = useState(new Set());
    const [calibrationData, setCalibrationData] = useState(() => {
        try {
            const storedData = sessionStorage.getItem('calibrationData');
            return storedData ? JSON.parse(storedData) : null;
        } catch (error) {
            console.error("Error reading calibration data from sessionStorage", error);
            return null;
        }
    });
    const [selectedPlot, setSelectedPlot] = useState([]);
    const [selectedTask, setSelectedTask] = useState(null);
    
    const [selectedTimepoint, setSelectedTimepoint] = useState(null);
    const [selectedCondition, setSelectedCondition] = useState(null);
    const [pcaSuggestions, setPcaSuggestions] = useState(() => {
        try {
            const storedData = sessionStorage.getItem('pcaSuggestions');
            return storedData ? JSON.parse(storedData) : null;
        } catch (error) {
            console.error("Error reading PCA suggestions from sessionStorage", error);
            return null;
        }
    });

        const [message, setMessage] = useState("");
    const deleteMessage = () => setMessage("");

    useEffect(() => {
        try {
            if (calibrationData) {
                sessionStorage.setItem('calibrationData', JSON.stringify(calibrationData));
            } else {
                sessionStorage.removeItem('calibrationData');
            }
        } catch (error) {
            console.error("Error saving calibration data to sessionStorage", error);
        }
    }, [calibrationData]);

    useEffect(() => {
        try {
            if (pcaSuggestions) {
                sessionStorage.setItem('pcaSuggestions', JSON.stringify(pcaSuggestions));
            } else {
                sessionStorage.removeItem('pcaSuggestions');
            }
        } catch (error) {
            console.error("Error saving PCA suggestions to sessionStorage", error);
        }
    }, [pcaSuggestions]);

    const value = {
        csvData,
        setCsvData,
        selectedMetrics,
        setSelectedMetrics,
        calibrationData,
        setCalibrationData,
        selectedPlot,
        setSelectedPlot,
        selectedTask,
        setSelectedTask,
        selectedTimepoint,         
        setSelectedTimepoint,      
        selectedCondition,         
        setSelectedCondition,
        message,
        setMessage,
        deleteMessage,      
        pcaSuggestions,
        setPcaSuggestions,
    };

    return (
        <DataContext.Provider value={value}>
            {children}
        </DataContext.Provider>
    );
}

export function useData() {
    const context = useContext(DataContext);
    if (context === null) {
        throw new Error('useData must be used within a DataProvider');
    }
    return context;
}
