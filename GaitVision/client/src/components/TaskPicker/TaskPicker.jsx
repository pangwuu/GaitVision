import React, { useEffect, useState } from "react";
import { useData } from "../DataContext/DataContext";

export default function TaskPicker() {
    const { calibrationData, csvData, selectedTask, setSelectedTask, selectedTimepoint, selectedCondition } = useData();
    const [tasks, setTasks] = useState([]);

    useEffect(() => {
        if (calibrationData && Array.isArray(csvData) && csvData.length > 0) {
            const filteredData = csvData.filter(row => 
                (!selectedTimepoint || row["Timepoint"] === selectedTimepoint) &&
                (!selectedCondition || row["Condition"] === selectedCondition)
            );
            const allTaskConditions = filteredData.map(row => row["Task condition"]);
            const nonEmptyTasks = allTaskConditions.filter(task => Boolean(task));
            const uniqueTasks = Array.from(new Set(nonEmptyTasks));
            setTasks(uniqueTasks);

            if (!selectedTask && uniqueTasks.length > 0){
                setSelectedTask(uniqueTasks[0]);
            } else if (selectedTask && !uniqueTasks.includes(selectedTask)) {
                setSelectedTask(uniqueTasks.length > 0 ? uniqueTasks[0] : null);
            }
        } else{
            setTasks([]);
            setSelectedTask(null);
        }
    }, [calibrationData, csvData, selectedTimepoint, selectedCondition, selectedTask, setSelectedTask]);

    // toggle selection
    const handleSelect = (task) => {
        setSelectedTask(task);
    };

    // No tasks available yet (i.e. before upload)
    if (tasks.length === 0){
        return(
            <div className="task-section">
                <h3 className="task-selection-title"> Walk Task Condition </h3>
                <div className="task-selection-list">
                    <div className="task-selection-empty"> No tasks available. </div>
                </div>
            </div>
        );
    }

    return(
        <div className="task-section">
            <h3 className="task-selection-title"> Walk Task Condition </h3>
            <div className="task-button-group">
                {tasks.map((task) => {
                    const activeClass= selectedTask === task ? "active" : "";
                    return(
                        <button
                            key={task}
                            className={`task-button ${activeClass}`}
                            onClick={() => handleSelect(task)}
                        >
                            {task}
                        </button>
                    );
                })}
            </div>
        </div>
    );
}