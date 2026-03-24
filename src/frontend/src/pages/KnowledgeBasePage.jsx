import { useEffect, useState, useMemo } from "react";
import Navbar from "../components/Navbar";
import KBPhaseCard from "../components/KBPhaseCard";
import "./KnowledgeBasePage.css";
import {
    fetchQueries as fetchQueriesApi,
    createOrUpdateQuery,
    deleteQuery as deleteQueryApi,
} from "../api/knowledgebase";
import { getAuthUrl, getStatus, syncFolder } from "../api/gdrive";

const PHASES = [
    { id: "P1", title: "Eligibility & Kickoff", phase: 1 },
    { id: "P2", title: "Scope & Technical Fit", phase: 2 },
    { id: "P3", title: "Evaluation Alignment", phase: 3 },
    { id: "P4", title: "Pricing & Submission", phase: 4 },
    { id: "P5", title: "Custom Queries", phase: 5 },
];

const KnowledgeBasePage = () => {
    const [queries, setQueries] = useState([]);
    const [expandedPhase, setExpandedPhase] = useState(null);
    const [gdriveConnected, setGdriveConnected] = useState(false);
    const [syncing, setSyncing] = useState(false);
    const [folderId, setFolderId] = useState("");
    const [syncedFiles, setSyncedFiles] = useState([]);

    const fetchQueries = async () => {
        const data = await fetchQueriesApi();
        const sorted = data.sort((a, b) => a.query_number - b.query_number);
        setQueries(sorted);
    };

    useEffect(() => {
        fetchQueries();
    }, []);

    useEffect(() => {
        getStatus().then(setGdriveConnected).catch(() => setGdriveConnected(false));
    }, []);

    const handleConnectGDrive = async () => {
        try {
            const authUrl = await getAuthUrl();
            window.location.href = authUrl;
        } catch (err) {
            console.error(err);
            alert("Failed to connect. Ensure GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET are set.");
        }
    };

    const handleSync = async () => {
        if (!folderId.trim()) {
            alert("Enter a Google Drive folder ID or folder URL");
            return;
        }
        setSyncing(true);
        try {
            const result = await syncFolder(folderId.trim());
            setSyncedFiles(result.files || []);
            fetchQueries();
        } catch (err) {
            alert(err.message || "Sync failed");
        } finally {
            setSyncing(false);
        }
    };

    const queriesByPhase = useMemo(() => {
        const grouped = {};
        PHASES.forEach((p) => {
            grouped[p.phase] = [];
        });
        queries.forEach((q) => {
            if (grouped[q.query_phase]) {
                grouped[q.query_phase].push(q);
            } else {
                grouped[5] = grouped[5] || [];
                grouped[5].push(q);
            }
        });
        return grouped;
    }, [queries]);

    const handleToggle = (phase) => {
        setExpandedPhase(expandedPhase === phase ? null : phase);
    };

    const handleAddQuery = async (queryData) => {
        const nextQueryNumber = Math.max(0, ...queries.map((q) => q.query_number)) + 1;
        const payload = {
            ...queryData,
            query_number: nextQueryNumber,
        };

        const success = await createOrUpdateQuery(payload, false);
        if (success) {
            await fetchQueries();
        }
        return success;
    };

    const handleEditQuery = async (queryData) => {
        const success = await createOrUpdateQuery(queryData, true);
        if (success) {
            await fetchQueries();
        }
        return success;
    };

    const handleDeleteQuery = async (queryNumber, queryPhase) => {
        if (queryPhase !== 5) return false;
        const success = await deleteQueryApi(queryNumber);
        if (success) {
            await fetchQueries();
        }
        return success;
    };

    return (
        <div className="kb-container">
            <Navbar />
            <div className="kb-page-content">
                <header className="kb-header">
                    <h1>
                        Knowledge <span>Base</span>
                    </h1>
                    <p>
                        Manage your RFP queries and knowledge base answers organized by capture phase.
                        Click on a phase to expand and add or edit queries.
                    </p>
                </header>

                <div className="gdrive-section">
                    <h3>Company Knowledge Base</h3>
                    {!gdriveConnected ? (
                        <button className="gdrive-connect-btn" onClick={handleConnectGDrive}>
                            Connect Google Drive
                        </button>
                    ) : (
                        <>
                            <p className="gdrive-status">Connected</p>
                            <div className="gdrive-sync-row">
                                <input
                                    type="text"
                                    placeholder="Folder ID or full Google Drive folder URL"
                                    value={folderId}
                                    onChange={(e) => setFolderId(e.target.value)}
                                    className="gdrive-folder-input"
                                />
                                <button
                                    className="gdrive-sync-btn"
                                    onClick={handleSync}
                                    disabled={syncing}
                                >
                                    {syncing ? "Syncing..." : "Sync Documents"}
                                </button>
                            </div>
                            {syncedFiles.length > 0 && (
                                <div className="gdrive-files-list">
                                    <span className="gdrive-files-label">Documents used as context:</span>
                                    <ul>
                                        {syncedFiles.map((name, i) => (
                                            <li key={i}>{name}</li>
                                        ))}
                                    </ul>
                                </div>
                            )}
                        </>
                    )}
                </div>

                <main className="kb-content">
                    <div className="kb-phases-grid">
                        {PHASES.map((phaseInfo) => (
                            <KBPhaseCard
                                key={phaseInfo.phase}
                                id={phaseInfo.id}
                                title={phaseInfo.title}
                                phase={phaseInfo.phase}
                                queries={queriesByPhase[phaseInfo.phase] || []}
                                isExpanded={expandedPhase === phaseInfo.phase}
                                onToggle={() => handleToggle(phaseInfo.phase)}
                                onAddQuery={handleAddQuery}
                                onEditQuery={handleEditQuery}
                                onDeleteQuery={handleDeleteQuery}
                            />
                        ))}
                    </div>
                </main>
            </div>
        </div>
    );
};

export default KnowledgeBasePage;
