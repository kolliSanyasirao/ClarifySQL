import { useEffect, useState } from "react";
import "./App.css";

// Vercel: set VITE_API_BASE_URL to your deployed Render backend URL.
// Local development falls back to the local FastAPI server.
const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000"
).replace(/\/+$/, "");

const categories = [
  { name: "SELECT Column", type: "Ambiguous", status: "completed" },
  { name: "VALUES Across Columns", type: "Ambiguous", status: "completed" },
  { name: "VALUES Within Column", type: "Ambiguous", status: "pending" },
  { name: "Vague Filter Term", type: "Ambiguous", status: "pending" },
  { name: "Nonexistent SELECT Column", type: "Unanswerable", status: "pending" },
  { name: "Nonexistent Value", type: "Unanswerable", status: "pending" },
  { name: "Nonexistent WHERE Column", type: "Unanswerable", status: "pending" },
  { name: "Unsupported Joins", type: "Unanswerable", status: "pending" },
];

function App() {
  const [activePage, setActivePage] = useState("Dashboard");
  useEffect(() => {
  const openExperiment = () => {
    setActivePage("Run Experiment");
  };

  const openResults = () => {
    setActivePage("Results");
  };

  const openPipeline = () => {
    setActivePage("Pipeline");
  };

  window.addEventListener(
    "open-run-experiment",
    openExperiment
  );

  window.addEventListener(
    "open-results",
    openResults
  );

  window.addEventListener(
    "open-pipeline",
    openPipeline
  );

  return () => {
    window.removeEventListener(
      "open-run-experiment",
      openExperiment
    );

    window.removeEventListener(
      "open-results",
      openResults
    );

    window.removeEventListener(
      "open-pipeline",
      openPipeline
    );
  };
}, []);

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">P</div>
          <div>
            <h1>ClarifySQL</h1>
            <span>Adaptive Clarification Engine</span>
          </div>
        </div>

        <nav>
          {["Dashboard", "Pipeline", "Run Experiment", "Results"].map((item) => (
            <button
              key={item}
              className={`nav-item ${activePage === item ? "active" : ""}`}
              onClick={() => setActivePage(item)}
            >
              <span className="nav-icon">
                {item === "Dashboard" && "⌂"}
                {item === "Pipeline" && "◈"}
                {item === "Run Experiment" && "▶"}
                {item === "Results" && "▤"}
              </span>
              {item}
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <div className="system-status">
            <span className="status-dot"></span>
            <div>
              <strong>System Ready</strong>
              <small>Local environment</small>
            </div>
          </div>
          <div className="version">ClarifySQL v1.0</div>
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <div>
            <p className="eyebrow">CLARIFYSQL RESEARCH WORKSPACE</p>
            <h2>{activePage}</h2>
          </div>

          <div className="top-actions">
            <div className="connection">
              <span className="status-dot"></span>
              Gemini Connected
            </div>
            <div className="avatar">PR</div>
          </div>
        </header>

        {activePage === "Dashboard" && <Dashboard />}
        {activePage === "Pipeline" && <Pipeline />}
        {activePage === "Run Experiment" && <RunExperiment />}
        {activePage === "Results" && <Results />}
      </main>
    </div>
  );
}
function Dashboard() {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadCategories = async () => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/categories`
      );

      if (!response.ok) {
        throw new Error("Failed to load category data");
      }

      const data = await response.json();
      setCategories(data || []);
    } catch (error) {
      console.error("Dashboard error:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCategories();

    const interval = setInterval(loadCategories, 3000);

    return () => clearInterval(interval);
  }, []);

  const ambiguousCategories = [
    "Ambiguous SELECT Column",
    "Ambiguous VALUES Across Columns",
    "Ambiguous VALUES Within Column",
    "Vague Filter Term",
  ];

  const unanswerableCategories = [
    "Nonexistent SELECT Column",
    "Nonexistent Value",
    "Nonexistent WHERE Column",
    "Unsupported Joins",
  ];

  const getCategory = (name) => {
    return categories.find((item) => item.name === name) || {
      name,
      count: 0,
      generated: false,
    };
  };

  const totalGenerated = categories.reduce(
    (sum, item) => sum + (item.count || 0),
    0
  );

  const completedCategories = categories.filter(
    (item) => item.count > 0
  ).length;

  const ambiguousGenerated = ambiguousCategories.reduce(
    (sum, name) => sum + getCategory(name).count,
    0
  );

  const unanswerableGenerated = unanswerableCategories.reduce(
    (sum, name) => sum + getCategory(name).count,
    0
  );

  const totalPossibleCategories = 8;

  return (
    <div className="page">

      {/* =====================================================
          HERO
         ===================================================== */}

      <section className="hero dashboard-hero">

        <div className="hero-copy">

          <div className="hero-badge">
            <span></span>
            RESEARCH PIPELINE ONLINE
          </div>
          <p className="hero-label">
  ADAPTIVE SCHEMA-GROUNDED CLARIFICATION
</p>

<h3>
  Understand the query.
  <br />
  Clarify the intent.
  <br />
  Generate valid SQL.
</h3>

<p className="hero-text">
  ClarifySQL is an adaptive, schema-grounded clarification engine
  for conversational Text-to-SQL systems. It identifies ambiguity,
  analyzes schema gaps, asks targeted clarification questions,
  and guides the query toward validated SQL.
</p>
         
          <div className="hero-actions">

            <button
              className="primary-btn"
              onClick={() => {
                window.dispatchEvent(
                  new CustomEvent("open-run-experiment")
                );
              }}
            >
              Start Experiment
              <span>→</span>
            </button>

            <button
              className="ghost-btn"
              onClick={() => {
                window.dispatchEvent(
                  new CustomEvent("open-results")
                );
              }}
            >
              Explore Results
            </button>

          </div>

        </div>

        <div className="hero-system">

          <div className="system-orbit orbit-a"></div>
          <div className="system-orbit orbit-b"></div>

          <div className="system-core">

  <div className="core-icon">
    C
  </div>

  <span>CLARIFYSQL ENGINE</span>

  <strong>
    {loading ? "Loading" : "Ready"}
  </strong>

  <div className="core-line">
    <span></span>
  </div>

  <small>
    Schema-Grounded AI
  </small>

</div>

         <div className="floating-node node-one">
  <span>01</span>
  JID
</div>

<div className="floating-node node-two">
  <span>02</span>
  SCG
</div>

<div className="floating-node node-three">
  <span>03</span>
  BRT
</div>

        </div>

      </section>

      {/* =====================================================
          KPI CARDS
         ===================================================== */}

      <section className="research-kpis">

        <div className="research-kpi">

          <div className="kpi-top">
            <span className="kpi-label">
              DATASET
            </span>

            <div className="kpi-icon">
              DB
            </div>
          </div>

          <strong>
            SPIDER
          </strong>

          <span className="kpi-status">
            <i></i>
            Dataset loaded
          </span>

        </div>


        <div className="research-kpi">

          <div className="kpi-top">
            <span className="kpi-label">
              LANGUAGE MODEL
            </span>

            <div className="kpi-icon">
              AI
            </div>
          </div>

          <strong>
            Gemini
          </strong>

          <span className="kpi-status">
            <i></i>
            API connected
          </span>

        </div>


        <div className="research-kpi">

          <div className="kpi-top">
            <span className="kpi-label">
              CATEGORY COVERAGE
            </span>

            <div className="kpi-icon">
              8
            </div>
          </div>

          <strong>
            {completedCategories} / {totalPossibleCategories}
          </strong>

          <span className="kpi-status neutral">
            {completedCategories} categories generated
          </span>

        </div>


        <div className="research-kpi featured-kpi">

          <div className="kpi-top">
            <span className="kpi-label">
              GENERATED EXAMPLES
            </span>

            <div className="kpi-icon">
              Σ
            </div>
          </div>

          <strong>
            {totalGenerated}
          </strong>

          <span className="kpi-status neutral">
            Across available experiments
          </span>

        </div>

      </section>


      {/* =====================================================
          OVERVIEW + COVERAGE
         ===================================================== */}

      <section className="dashboard-grid">

        {/* LEFT */}
        <div className="panel overview-panel">

          <div className="panel-header">

            <div>
              <p className="panel-kicker">
                RESEARCH OVERVIEW
              </p>

              <h4>
                Generation summary
              </h4>
            </div>

            <span className="live-pill">
              <i></i>
              LIVE
            </span>

          </div>

          <div className="overview-content">

            <div className="overview-total">
              <span>
                Total generated examples
              </span>

              <strong>
                {totalGenerated}
              </strong>

              <small>
                Real records available through the PRACTIQ backend
              </small>
            </div>

            <div className="overview-split">

              <div className="overview-item">
                <span className="overview-dot ambiguous"></span>

                <div>
                  <strong>
                    {ambiguousGenerated}
                  </strong>

                  <small>
                    Ambiguous examples
                  </small>
                </div>
              </div>


              <div className="overview-item">
                <span className="overview-dot unanswerable"></span>

                <div>
                  <strong>
                    {unanswerableGenerated}
                  </strong>

                  <small>
                    Unanswerable examples
                  </small>
                </div>
              </div>

            </div>

          </div>

        </div>


        {/* RIGHT */}
        <div className="panel coverage-panel">

          <div className="panel-header">

            <div>
              <p className="panel-kicker">
                CATEGORY COVERAGE
              </p>

              <h4>
                Generation progress
              </h4>
            </div>

            <span className="coverage-total">
              {completedCategories}/{totalPossibleCategories}
            </span>

          </div>

          <div className="coverage-list">

            {ambiguousCategories.map((name) => {
              const item = getCategory(name);

              return (
                <CoverageBar
                  key={name}
                  name={name.replace("Ambiguous ", "")}
                  count={item.count}
                  completed={item.count > 0}
                />
              );
            })}

            <div className="coverage-divider"></div>

            {unanswerableCategories.map((name) => {
              const item = getCategory(name);

              return (
                <CoverageBar
                  key={name}
                  name={name}
                  count={item.count}
                  completed={item.count > 0}
                />
              );
            })}

          </div>

        </div>

      </section>


      {/* =====================================================
          PIPELINE
         ===================================================== */}

      <section className="panel workflow-panel">

        <div className="panel-header">

          <div>
            <p className="panel-kicker">
              END-TO-END WORKFLOW
            </p>

            <h4>
              How PRACTIQ generates the dataset
            </h4>
          </div>

          <span className="workflow-caption">
            Research pipeline
          </span>

        </div>


        <div className="workflow">

          <WorkflowNode
            number="01"
            title="SPIDER"
            description="Benchmark dataset"
            active
          />

          <WorkflowArrow />

          <WorkflowNode
            number="02"
            title="SCHEMA"
            description="Modify database"
          />

          <WorkflowArrow />

          <WorkflowNode
            number="03"
            title="GEMINI"
            description="Generate dialogue"
            active
          />

          <WorkflowArrow />

          <WorkflowNode
            number="04"
            title="SQL"
            description="Validate queries"
          />

          <WorkflowArrow />

          <WorkflowNode
            number="05"
            title="OUTPUT"
            description="Final dataset"
            active
          />

        </div>

      </section>


      {/* =====================================================
          FACULTY QUICK ACTIONS
         ===================================================== */}

      <section className="quick-actions">

        <button
          className="quick-action"
          onClick={() => {
            window.dispatchEvent(
              new CustomEvent("open-run-experiment")
            );
          }}
        >
          <div className="quick-icon">
            ▶
          </div>

          <div>
            <strong>
              Run Experiment
            </strong>

            <span>
              Start a new PRACTIQ generation
            </span>
          </div>

          <b>→</b>
        </button>


        <button
          className="quick-action"
          onClick={() => {
            window.dispatchEvent(
              new CustomEvent("open-results")
            );
          }}
        >
          <div className="quick-icon">
            ≡
          </div>

          <div>
            <strong>
              Explore Results
            </strong>

            <span>
              Inspect generated conversations
            </span>
          </div>

          <b>→</b>
        </button>


        <button
          className="quick-action"
          onClick={() => {
            window.dispatchEvent(
              new CustomEvent("open-pipeline")
            );
          }}
        >
          <div className="quick-icon">
            ◈
          </div>

          <div>
            <strong>
              View Pipeline
            </strong>

            <span>
              Understand the research workflow
            </span>
          </div>

          <b>→</b>
        </button>

      </section>

    </div>
  );
}


function CoverageBar({ name, count, completed }) {
  const width = completed
    ? Math.min(100, Math.max(12, count * 7))
    : 0;

  return (
    <div className="coverage-item">

      <div className="coverage-meta">

        <div className="coverage-name">
          <span
            className={`coverage-check ${
              completed ? "done" : ""
            }`}
          >
            {completed ? "✓" : ""}
          </span>

          <strong>
            {name}
          </strong>
        </div>

        <span className="coverage-count">
          {count > 0 ? count : "—"}
        </span>

      </div>

      <div className="coverage-track">

        <div
          className={`coverage-fill ${
            completed ? "filled" : ""
          }`}
          style={{
            width: `${width}%`,
          }}
        />

      </div>

    </div>
  );
}


function WorkflowNode({
  number,
  title,
  description,
  active = false,
}) {
  return (
    <div className={`workflow-node ${active ? "active" : ""}`}>

      <div className="workflow-number">
        {number}
      </div>

      <strong>
        {title}
      </strong>

      <span>
        {description}
      </span>

    </div>
  );
}


function WorkflowArrow() {
  return (
    <div className="workflow-arrow">
      <span></span>
      →
    </div>
  );
}

function CategoryRow({ name, status }) {
  return (
    <div className="category-row">
      <div className="category-icon">{status === "completed" ? "✓" : "○"}</div>
      <div className="category-info">
        <strong>{name}</strong>
        <span>{status === "completed" ? "Generation completed" : "Not generated yet"}</span>
      </div>
      <div className={`category-status ${status}`}>
        {status === "completed" ? "Completed" : "Pending"}
      </div>
    </div>
  );
}

function Stat({ title, value, detail }) {
  return (
    <div className="stat-card">
      <span>{title}</span>
      <strong>{value}</strong>
      <small>{detail}</small>
    </div>
  );
}

function ArchitectureStep({ number, title, text }) {
  return (
    <div className="architecture-step">
      <span>{number}</span>
      <strong>{title}</strong>
      <small>{text}</small>
    </div>
  );
}

function Pipeline() {
  return (
    <div className="page">
      <section className="page-intro">
        <p className="panel-kicker">PIPELINE</p>
        <h3>End-to-end generation workflow</h3>
        <p>
          Follow every stage of the PRACTIQ data generation process from
          dataset selection to validated output.
        </p>
      </section>

      <div className="pipeline-large">
        {[
          ["01", "SPIDER Dataset", "Load questions and database schemas", "done"],
          ["02", "Question Selection", "Select questions for processing", "done"],
          ["03", "Schema Modification", "Create ambiguity or unanswerable conditions", "done"],
          ["04", "LLM Generation", "Generate follow-up conversations", "current"],
          ["05", "SQL Validation", "Execute and validate generated SQL", "pending"],
          ["06", "Final Dataset", "Store contextualized JSONL output", "pending"],
        ].map(([num, title, text, status]) => (
          <div className="pipeline-large-row" key={num}>
            <div className={`pipeline-number ${status}`}>{num}</div>
            <div>
              <strong>{title}</strong>
              <p>{text}</p>
            </div>
            <span className={`pipeline-state ${status}`}>
              {status === "done" ? "Completed" : status === "current" ? "Running" : "Pending"}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}


function RunExperiment() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Hello! I’m ClarifySQL. Ask me a natural-language question about the available databases. I’ll identify the relevant schema, detect ambiguity, ask for clarification when needed, and generate validated SQL.",
      stage: "JID",
    },
  ]);

  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const [database, setDatabase] = useState("");

  const sendMessage = async () => {
    const text = input.trim();

    if (!text || sending) return;

    const userMessage = {
      role: "user",
      content: text,
    };

    const updatedMessages = [
      ...messages,
      userMessage,
    ];

    setMessages(updatedMessages);
    setInput("");
    setSending(true);

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/chat`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            message: text,
            history: updatedMessages,
            database: database || null,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Request failed"
        );
      }

      setAnalysis(data);

      if (data.database) {
        setDatabase(data.database);
      }

      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content:
            data.message ||
            "I need more information to continue.",
          stage: data.stage || "JID",
        },
      ]);
    } catch (error) {
      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content:
            error.message ||
            "Unable to connect to ClarifySQL.",
          stage: "ERROR",
        },
      ]);
    } finally {
      setSending(false);
    }
  };

  const handleKeyDown = (event) => {
    if (
      event.key === "Enter" &&
      !event.shiftKey
    ) {
      event.preventDefault();
      sendMessage();
    }
  };

  const clearChat = () => {
    setMessages([
      {
        role: "assistant",
        content:
          "Conversation cleared. Ask me a new database question.",
        stage: "JID",
      },
    ]);

    setAnalysis(null);
    setDatabase("");
  };

  return (
    <div className="chat-page">

      {/* HEADER */}

      <section className="chat-header">

        <div>
          <p className="panel-kicker">
            CLARIFYSQL ASSISTANT
          </p>

          <h3>
            Conversational SQL Workspace
          </h3>

          <p>
            Ask a natural-language question and
            ClarifySQL will analyze intent, inspect
            the schema, resolve ambiguity, generate
            SQL, and validate the result.
          </p>
        </div>

        <div className="chat-header-actions">

          <div className="engine-pill">
            <i></i>
            Gemini Connected
          </div>

          <button
            className="secondary-btn"
            onClick={clearChat}
          >
            Clear
          </button>

        </div>

      </section>


      {/* WORKSPACE */}

      <section className="chat-workspace">

        {/* LEFT CHAT */}

        <div className="chat-main">

          <div className="chat-messages">

            {messages.map((message, index) => (

              <div
                key={index}
                className={`chat-message ${
                  message.role
                }`}
              >

                <div className="chat-avatar">
                  {message.role === "user"
                    ? "YOU"
                    : "C"}
                </div>

                <div className="chat-content">

                  <div className="chat-meta">

                    <strong>
                      {message.role === "user"
                        ? "You"
                        : "ClarifySQL"}
                    </strong>

                    <span>
                      {message.stage}
                    </span>

                  </div>

                  <div className="chat-bubble">
                    {message.content}
                  </div>

                </div>

              </div>

            ))}


            {sending && (

              <div className="chat-message assistant">

                <div className="chat-avatar">
                  C
                </div>

                <div className="chat-content">

                  <div className="chat-meta">
                    <strong>
                      ClarifySQL
                    </strong>

                    <span>
                      ANALYZING
                    </span>
                  </div>

                  <div className="chat-bubble typing">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>

                </div>

              </div>

            )}

          </div>


          {/* INPUT */}

          <div className="chat-composer">

            <textarea
              value={input}
              onChange={(event) =>
                setInput(event.target.value)
              }
              onKeyDown={handleKeyDown}
              placeholder="Ask a database question..."
              rows={2}
              disabled={sending}
            />

            <button
              className="send-button"
              onClick={sendMessage}
              disabled={
                sending || !input.trim()
              }
            >
              {sending ? "..." : "Send →"}
            </button>

          </div>


          {/* EXAMPLES */}

          <div className="example-prompts">

            <span>Try:</span>

            <button
              onClick={() =>
                setInput(
                  "Show me the students"
                )
              }
            >
              Show me the students
            </button>

            <button
              onClick={() =>
                setInput(
                  "What is the average age of students?"
                )
              }
            >
              Average age of students
            </button>

            <button
              onClick={() =>
                setInput(
                  "List the student details"
                )
              }
            >
              List student details
            </button>

          </div>

        </div>


        {/* RIGHT ANALYSIS PANEL */}

        <aside className="chat-analysis">

          <div className="analysis-header">

            <p className="panel-kicker">
              CLARIFYSQL PIPELINE
            </p>

            <h4>
              Query Analysis
            </h4>

          </div>


          {/* DATABASE */}

          <div className="analysis-db">

            <span>
              SELECTED DATABASE
            </span>

            <strong>
              {analysis?.database ||
                database ||
                "Auto Detect"}
            </strong>

            <small>
              SPIDER schema search
            </small>

          </div>


          {/* PIPELINE */}

          <div className="analysis-steps">

            <AnalysisStep
              number="01"
              title="JID"
              text="Intent detection"
              active={
                analysis?.stage === "JID" ||
                analysis?.stage === "SCG" ||
                analysis?.stage === "CLARIFY" ||
                analysis?.stage === "SQL"
              }
            />

            <AnalysisStep
              number="02"
              title="SCG"
              text="Schema gap analysis"
              active={
                analysis?.stage === "SCG" ||
                analysis?.stage === "CLARIFY" ||
                analysis?.stage === "SQL"
              }
            />

            <AnalysisStep
              number="03"
              title="POLICY"
              text="Clarification decision"
              active={
                analysis?.stage === "CLARIFY" ||
                analysis?.stage === "SQL"
              }
            />

            <AnalysisStep
              number="04"
              title="BRT"
              text="Dialogue context"
              active={
                analysis?.stage === "SQL"
              }
            />

            <AnalysisStep
              number="05"
              title="SQL"
              text="Generate & validate"
              active={
                analysis?.stage === "SQL"
              }
            />

          </div>


          {/* SQL */}

          {analysis?.sql && (

            <div className="analysis-sql">

              <div className="sql-title">
                VALIDATED SQL
              </div>

              <pre>
                {analysis.sql}
              </pre>

            </div>

          )}


          {/* RESULT */}

          {analysis?.rows && (

            <div className="analysis-result">

              <div className="sql-title">
                DATABASE RESULT
              </div>

              <div className="result-count">
                {analysis.rows.length} row
                {analysis.rows.length !== 1
                  ? "s"
                  : ""}
              </div>

              <div className="result-preview">

                {analysis.rows
                  .slice(0, 5)
                  .map((row, index) => (

                    <div
                      key={index}
                      className="result-row"
                    >

                      {Object.entries(row).map(
                        ([key, value]) => (

                          <span key={key}>
                            <b>{key}</b>
                            {String(value)}
                          </span>

                        )
                      )}

                    </div>

                  ))}

              </div>

            </div>

          )}

        </aside>

      </section>

    </div>
  );
}


function AnalysisStep({
  number,
  title,
  text,
  active,
}) {
  return (
    <div
      className={`analysis-step ${
        active ? "active" : ""
      }`}
    >

      <div className="analysis-number">
        {number}
      </div>

      <div>
        <strong>{title}</strong>
        <span>{text}</span>
      </div>

      <i>
        {active ? "✓" : "○"}
      </i>

    </div>
  );
}
function Results() {
  const [category, setCategory] = useState("Ambiguous SELECT Column");
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(0);
  const [search, setSearch] = useState("");

  const categories = [
    "Ambiguous SELECT Column",
    "Ambiguous VALUES Across Columns",
    "Ambiguous VALUES Within Column",
    "Vague Filter Term",
    "Nonexistent SELECT Column",
    "Nonexistent Value",
    "Nonexistent WHERE Column",
    "Unsupported Joins",
  ];

  useEffect(() => {
    setLoading(true);
    setSelected(0);

    fetch(
      `${API_BASE_URL}/api/results?category=${encodeURIComponent(
        category
      )}`
    )
      .then((res) => res.json())
      .then((json) => {
        setData(json.results || []);
      })
      .catch((error) => {
        console.error("Failed to load results:", error);
        setData([]);
      })
      .finally(() => {
        setLoading(false);
      });
  }, [category]);

  const filteredData = data.filter((item) =>
    (item.question || "")
      .toLowerCase()
      .includes(search.toLowerCase())
  );

  const selectedItem = filteredData[selected];

  const downloadResults = () => {
    const blob = new Blob(
      [data.map((item) => JSON.stringify(item)).join("\n")],
      { type: "application/jsonl" }
    );

    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");

    a.href = url;
    a.download = `${category.replaceAll(" ", "_")}.jsonl`;
    a.click();

    URL.revokeObjectURL(url);
  };

  return (
    <div className="page">

      <section className="page-intro">
        <p className="panel-kicker">RESULT EXPLORER</p>

        <div className="results-title-row">
          <div>
            <h3>ClarifySQL</h3>
            <p>
              Explore, search and export generated conversational
              Text-to-SQL examples.
            </p>
          </div>

          <button
            className="secondary-btn"
            onClick={downloadResults}
            disabled={!data.length}
          >
            ↓ Download JSONL
          </button>
        </div>
      </section>

      <div className="result-toolbar">

        <div className="toolbar-group">
          <label>Category</label>

          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
          >
            {categories.map((item) => (
              <option key={item}>{item}</option>
            ))}
          </select>
        </div>

        <div className="toolbar-group search-group">
          <label>Search</label>

          <input
            type="text"
            placeholder="Search questions..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setSelected(0);
            }}
          />
        </div>

      </div>

      {loading ? (
        <div className="empty-state">
          <div className="loading-spinner"></div>
          <h4>Loading results</h4>
          <p>Reading PRACTIQ generated data...</p>
        </div>
      ) : filteredData.length === 0 ? (
        <div className="empty-state">
          <h4>No examples found</h4>
          <p>
            There are no results matching the current category/search.
          </p>
        </div>
      ) : (
        <div className="results-layout">

          <div className="result-list-panel">

            <div className="result-list-header">
              <strong>Examples</strong>
              <span>{filteredData.length}</span>
            </div>

            {filteredData.map((result, index) => (
              <button
                key={index}
                className={`result-list-item ${
                  selected === index ? "selected" : ""
                }`}
                onClick={() => setSelected(index)}
              >
                <span className="result-number">
                  {String(index + 1).padStart(2, "0")}
                </span>

                <span className="result-question">
                  {result.question || "Untitled question"}
                </span>
              </button>
            ))}

          </div>

          <ResultDetails item={selectedItem} />

        </div>
      )}
    </div>
  );
}
function ResultDetails({ item }) {
  if (!item) return null;

  const conversation =
    item.ambiguousUnanswerableConversation || {};

  const finalConversation =
    conversation
      .rephrased_explanation_selected_followup_sql_complete_conversation ||
    [];

  const validFollowups =
    conversation
      .valid_ranked_response_with_followup_sql_parsed || [];

  const removedColumns =
    item.schemaModification?.removeColumn || [];

  return (
    <div className="result-detail-panel">

      <div className="detail-top">
        <div>
          <p className="panel-kicker">DATABASE</p>
          <h4>{item.db_id}</h4>
        </div>

        <span className="category-badge">
          {item.ambiguousUnanswerableCategory}
        </span>
      </div>

      <ResultBlock title="Original Question">
        {item.question}
      </ResultBlock>

      <ResultBlock title="Schema Modification">
        <div className="schema-tags">
          {removedColumns.map((column, index) => (
            <span className="tag" key={index}>
              {column.table}.{column.column}
            </span>
          ))}
        </div>
      </ResultBlock>

      {finalConversation.length > 1 && (
        <ResultBlock title="DB Expert Explanation">
          {finalConversation[1]?.["DB EXPERT"]}
        </ResultBlock>
      )}

      {validFollowups.length > 0 && (
        <ResultBlock title="Generated Follow-up">
          <div className="followup-box">
            <strong>
              {validFollowups[0]?.USER}
            </strong>

            <div className="sql-box small-sql">
              <div className="sql-header">
                <span>GENERATED SQL</span>
              </div>

              <pre>
                {validFollowups[0]?.["DB EXPERT"]}
              </pre>
            </div>
          </div>
        </ResultBlock>
      )}

      {validFollowups.length > 0 &&
        validFollowups[0]?.SQL_EXECUTION_RESULTS && (
          <ResultBlock title="SQL Execution Result">
            <div className="execution-result">
              {JSON.stringify(
                validFollowups[0].SQL_EXECUTION_RESULTS
              )}
            </div>
          </ResultBlock>
        )}

    </div>
  );
}

function ResultBlock({ title, children }) {
  return (
    <div className="result-block">
      <p>{title}</p>
      <div>{children}</div>
    </div>
  );
}

export default App;