"use client";
import { useState, useEffect } from "react";
import styles from "./admin.module.css";
import { AuthGuard, useAuth } from "../../lib/auth-context";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "https://abhirva-backend.onrender.com";

// ---------------------------------------------------------------------------
// Admin Portal Content (protected by AuthGuard ADMIN role)
// ---------------------------------------------------------------------------
function AdminPortalContent() {
  const { profile } = useAuth();
  const [students, setStudents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const [selectedStudentId, setSelectedStudentId] = useState<string>("");
  const [studentSubscriptions, setStudentSubscriptions] = useState<any[]>([]);
  const [loadingSubscriptions, setLoadingSubscriptions] = useState(false);

  const [parents, setParents] = useState<any[]>([]);
  const [parentConnections, setParentConnections] = useState<Record<string, string[]>>({});
  const [selectedParentId, setSelectedParentId] = useState<string>("");
  const [connectionStudentId, setConnectionStudentId] = useState<string>("");

  const [grantCategory, setGrantCategory] = useState("10th Class");
  const [grantSubject, setGrantSubject] = useState("Maths");
  const [grantGrade, setGrantGrade] = useState("Grade 10");
  const [genCategory, setGenCategory] = useState("10th Class");
  const [genGrade, setGenGrade] = useState("Grade 1");
  const [genSubject, setGenSubject] = useState("SST");
  const [genTopic, setGenTopic] = useState("");
  const [genYear, setGenYear] = useState("2023");
  const [libGrade, setLibGrade] = useState("Grade 1");
  const [libLanguage, setLibLanguage] = useState("English");
  const [topics, setTopics] = useState<string[]>([]);
  const [loadingTopics, setLoadingTopics] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [numQuestions, setNumQuestions] = useState(10);
  const [sstSubSubject, setSstSubSubject] = useState("History");
  const [isComprehension, setIsComprehension] = useState(false);

  // Fetch all students
  useEffect(() => {
    fetch(`${BACKEND_URL}/api/admin/students`)
      .then(res => res.json())
      .then(data => {
        if (data.status === "success") setStudents(data.students);
        setLoading(false);
      })
      .catch(err => { console.error(err); setLoading(false); });

    fetch(`${BACKEND_URL}/api/admin/parents`)
      .then(res => res.json())
      .then(data => { if (data.status === "success") setParents(data.parents || []); });
    fetchConnections();
  }, []);

  const fetchConnections = () => {
    fetch(`${BACKEND_URL}/api/admin/parent-connections`)
      .then(res => res.json())
      .then(data => { if (data.status === "success") setParentConnections(data.connections || {}); });
  };

  // Fetch subscriptions when student is selected
  useEffect(() => {
    if (selectedStudentId) {
      fetchSubscriptions(selectedStudentId);
    } else {
      setStudentSubscriptions([]);
    }
  }, [selectedStudentId]);

  const fetchSubscriptions = (profileId: string) => {
    setLoadingSubscriptions(true);
    fetch(`${BACKEND_URL}/api/admin/student/${profileId}/access`, { cache: 'no-store' })
      .then(res => res.json())
      .then(data => {
        if (data.status === "success") setStudentSubscriptions(data.subscriptions);
        setLoadingSubscriptions(false);
      })
      .catch(err => { console.error(err); setLoadingSubscriptions(false); });
  };

  // Fetch topics for quiz generation
  useEffect(() => {
    setLoadingTopics(true);
    let url = `${BACKEND_URL}/api/admin/topics?subject=${encodeURIComponent(genSubject)}&category=${encodeURIComponent(genCategory)}`;
    if (genSubject === "SST") url += `&sst_sub_subject=${encodeURIComponent(sstSubSubject)}`;
    if (genCategory === "Book Library") {
      url = `${BACKEND_URL}/api/library/books?grade=${encodeURIComponent(libGrade)}&language=${encodeURIComponent(libLanguage)}`;
    }
    fetch(url)
      .then(res => res.json())
      .then(data => {
        if (data.status === "success") {
          const newTopics = genCategory === "Book Library" ? data.books : data.topics;
          setTopics(newTopics || []);
          if (newTopics?.length > 0) setGenTopic(newTopics[0]);
          else setGenTopic("");
        }
        setLoadingTopics(false);
      })
      .catch(err => { console.error("Failed to fetch topics", err); setLoadingTopics(false); });
  }, [genCategory, genSubject, sstSubSubject, libGrade, libLanguage]);

  const handleAddConnection = async () => {
    if (!selectedParentId || !connectionStudentId) return;
    try {
      const res = await fetch(`${BACKEND_URL}/api/admin/parent-connection`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ parent_id: selectedParentId, student_id: connectionStudentId })
      });
      if (res.ok) fetchConnections();
    } catch (e) {}
  };

  const handleRemoveConnection = async (parentId: string, studentId: string) => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/admin/parent-connection?parent_id=${parentId}&student_id=${studentId}`, {
        method: "DELETE"
      });
      if (res.ok) fetchConnections();
    } catch (e) {}
  };

  const handleDeleteStudent = async (id: string) => {
    if (!confirm("Are you sure you want to delete this student? This action cannot be undone.")) return;
    
    try {
      const res = await fetch(`${BACKEND_URL}/api/admin/student/${id}`, {
        method: "DELETE",
      });
      const data = await res.json();
      if (res.ok && data.status === "success") {
        alert("✅ Student deleted successfully");
        setStudents(prev => prev.filter(s => s.id !== id));
        if (selectedStudentId === id) {
          setSelectedStudentId("");
          setStudentSubscriptions([]);
        }
      } else {
        alert(data.message || "Failed to delete student.");
      }
    } catch (err: any) {
      console.error(err);
      alert(`Error deleting student: ${err.message || err}`);
    }
  };

  const handleGrantAccess = async (id: string) => {
    let packageId = "";
    if (grantCategory === "10th Class") packageId = `10th Board ${grantSubject} Booster`;
    else if (grantCategory === "IMO Test") packageId = `IMO ${grantGrade}`;
    else if (grantCategory === "Book Library") packageId = "Book Library";
    else if (grantCategory === "Chess") packageId = "Chess Tutor";

    try {
      const res = await fetch(`${BACKEND_URL}/api/admin/grant`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          admin_id: profile?.id || "admin",
          target_profile_id: id,
          package_name: packageId,
        }),
      });
      const data = await res.json();
      if (data.status === "success") {
        alert(`✅ Subscription for "${packageId}" granted successfully!`);
        fetchSubscriptions(id);
      } else {
        alert(data.message || "Failed to grant subscription");
      }
    } catch (err) {
      console.error(err);
      alert("Error granting subscription");
    }
  };

  // MODULE 4 FIX: Pass package ID (not just name) for reliable revoke
  const handleRevokeSpecificAccess = async (profileId: string, packageId: string, packageName: string) => {
    if (!confirm(`Revoke "${packageName}" from this student?`)) return;

    try {
      const res = await fetch(`${BACKEND_URL}/api/admin/revoke`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          admin_id: profile?.id || "admin",
          target_profile_id: profileId,
          package_id: packageId,    // Pass the DB UUID for reliable matching
          package_name: packageName, // Also send name as fallback
        }),
      });
      const data = await res.json();
      if (res.ok && data.status === "success") {
        alert(`✅ Access to "${packageName}" revoked successfully.`);
        // Immediately update UI
        setStudentSubscriptions(prev => prev.filter(sub => sub.id !== packageId));
      } else {
        alert(data.message || data.detail || "Failed to revoke subscription.");
      }
    } catch (err: any) {
      console.error(err);
      alert(`Error revoking: ${err.message || err}`);
    }
  };

  const handleGenerateQuiz = async () => {
    setGenerating(true);
    try {
      let res, data;
      if (genCategory === "Past Papers") {
        res = await fetch(`${BACKEND_URL}/api/admin/generate_past_paper`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            board: "CBSE",
            grade: "10th Class",
            subject: genSubject,
            year: genYear,
            num_questions: numQuestions,
          }),
        });
      } else if (genCategory === "Book Library") {
        res = await fetch(`${BACKEND_URL}/api/library/quiz/generate`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ grade: libGrade, language: libLanguage, book: genTopic, num_questions: numQuestions }),
        });
      } else {
        res = await fetch(`${BACKEND_URL}/api/admin/generate_quiz`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            board: "CBSE",
            grade: genCategory === "IMO Test" ? genGrade : genCategory,
            subject: genSubject === "SST" ? sstSubSubject : (genCategory === "IMO Test" ? "IMO" : genSubject),
            chapter: genTopic,
            num_questions: numQuestions,
            quiz_type: (genSubject === "English" && isComprehension) ? "Comprehension" : "Standard"
          }),
        });
      }
      data = await res.json();
      if (data.status === "success") alert("✅ Quiz generated and saved to database!");
      else alert("Error: " + (data.detail || data.error || data.message || "Unknown error"));
    } catch (err) {
      console.error(err);
      alert("Failed to generate quiz");
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className={styles.adminContainer}>
      <header className={styles.header}>
        <h1>Admin <span className="gradient-text">Control Center</span></h1>
        <p style={{ color: "var(--text-secondary)" }}>
          Logged in as: <strong>{profile?.full_name}</strong>
        </p>
      </header>

      {/* Quiz Generator */}
      <div className={`glass-panel ${styles.section}`} style={{ marginBottom: "2rem" }}>
        <h2 className={styles.sectionTitle}>🧪 Quiz Generator</h2>
        <div style={{ display: "flex", gap: "1rem", marginBottom: "1rem", flexWrap: "wrap" }}>
          <select value={genCategory} onChange={(e) => setGenCategory(e.target.value)} style={{ padding: "0.5rem", borderRadius: "4px", border: "1px solid #ccc", flex: "1 1 200px", color: "black" }}>
            <option value="10th Class">10th Class</option>
            <option value="IMO Test">IMO Test</option>
            <option value="Book Library">Book Library</option>
            <option value="Past Papers">Past Papers</option>
          </select>

          {genCategory === "IMO Test" && (
            <select value={genGrade} onChange={(e) => setGenGrade(e.target.value)} style={{ padding: "0.5rem", borderRadius: "4px", border: "1px solid #ccc", flex: "1 1 200px", color: "black" }}>
              {[...Array(10)].map((_, i) => (<option key={i} value={`Grade ${i + 1}`}>Grade {i + 1}</option>))}
            </select>
          )}

          {genCategory === "Book Library" && (
            <>
              <select value={libGrade} onChange={(e) => setLibGrade(e.target.value)} style={{ padding: "0.5rem", borderRadius: "4px", border: "1px solid #ccc", flex: "1 1 200px", color: "black" }}>
                {["Kindergarten", "Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5", "Grade 6", "Grade 7", "Grade 8"].map(g => (<option key={g} value={g}>{g}</option>))}
              </select>
              <select value={libLanguage} onChange={(e) => setLibLanguage(e.target.value)} style={{ padding: "0.5rem", borderRadius: "4px", border: "1px solid #ccc", flex: "1 1 200px", color: "black" }}>
                <option value="English">English</option>
                <option value="Marathi">Marathi</option>
                <option value="Hindi">Hindi</option>
              </select>
            </>
          )}

          {(genCategory === "10th Class" || genCategory === "Past Papers") && (
            <select value={genSubject} onChange={(e) => setGenSubject(e.target.value)} style={{ padding: "0.5rem", borderRadius: "4px", border: "1px solid #ccc", flex: "1 1 200px", color: "black" }}>
              {["English", "Maths", "SST", "Science", "Computers", "Marathi"].map(s => (<option key={s} value={s}>{s}</option>))}
            </select>
          )}

          {genCategory === "Past Papers" && (
            <select value={genYear} onChange={(e) => setGenYear(e.target.value)} style={{ padding: "0.5rem", borderRadius: "4px", border: "1px solid #ccc", flex: "1 1 200px", color: "black" }}>
              {["2024", "2023", "2022", "2021", "2020", "2019", "2018"].map(y => (<option key={y} value={y}>{y}</option>))}
            </select>
          )}

          {genCategory === "10th Class" && genSubject === "SST" && (
            <select value={sstSubSubject} onChange={(e) => setSstSubSubject(e.target.value)} style={{ padding: "0.5rem", borderRadius: "4px", border: "1px solid #ccc", flex: "1 1 200px", color: "black" }}>
              {["Economics", "Geography", "History", "Political Science"].map(s => (<option key={s} value={s}>{s}</option>))}
            </select>
          )}

          {genCategory === "10th Class" && genSubject === "English" && (
            <label style={{ display: "flex", alignItems: "center", gap: "0.5rem", padding: "0.5rem", borderRadius: "4px", border: "1px solid #ccc", background: "rgba(255,255,255,0.1)" }}>
              <input type="checkbox" checked={isComprehension} onChange={(e) => setIsComprehension(e.target.checked)} />
              Reading Comprehension
            </label>
          )}

          <input type="number" value={numQuestions} onChange={(e) => setNumQuestions(Number(e.target.value))} min="1" max="50" style={{ padding: "0.5rem", borderRadius: "4px", border: "1px solid #ccc", flex: "0 1 100px", color: "black" }} title="Number of Questions" />

          {genCategory !== "Past Papers" && (
            <select value={genTopic} onChange={(e) => setGenTopic(e.target.value)} style={{ padding: "0.5rem", borderRadius: "4px", border: "1px solid #ccc", flex: "1 1 200px", color: "black" }} disabled={loadingTopics || topics.length === 0}>
              {loadingTopics ? <option value="">Loading topics...</option>
                : topics.length === 0 ? <option value="">No topics found</option>
                : topics.map((t, i) => (<option key={i} value={t}>{t}</option>))}
            </select>
          )}

          <button className={styles.grantBtn} onClick={handleGenerateQuiz} disabled={generating || (genCategory !== "Past Papers" && !genTopic && topics.length === 0)}>
            {generating ? "Generating..." : "Generate & Save to Database"}
          </button>
        </div>
      </div>

      {/* Student Management */}
      <div className={`glass-panel ${styles.section}`}>
        <h2 className={styles.sectionTitle}>👥 Student Management</h2>

        {loading ? (
          <p>Loading students from database...</p>
        ) : (
          <div style={{ marginBottom: "1.5rem" }}>
            <label style={{ display: "block", marginBottom: "0.5rem" }}>Select a Student:</label>
            <select
              value={selectedStudentId}
              onChange={(e) => setSelectedStudentId(e.target.value)}
              style={{ padding: "0.75rem", borderRadius: "8px", border: "1px solid #ccc", width: "100%", maxWidth: "400px", color: "black", fontSize: "1rem" }}
            >
              <option value="">-- Select a Student --</option>
              {students.map(student => (
                <option key={student.id} value={student.id}>
                  {student.full_name || student.name || student.id.substring(0, 8)}
                </option>
              ))}
            </select>
          </div>
        )}

        {selectedStudentId && (
          <div className={styles.studentDetailsPanel} style={{ marginTop: "2rem", padding: "1.5rem", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "12px", background: "rgba(0,0,0,0.2)" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
              <h3 style={{ color: "var(--primary-color)", margin: 0 }}>Current Active Subscriptions</h3>
              <button onClick={() => handleDeleteStudent(selectedStudentId)} style={{ background: "transparent", border: "1px solid #ff4d4d", color: "#ff4d4d", padding: "0.4rem 1rem", borderRadius: "4px", cursor: "pointer" }}>🗑️ Delete Student</button>
            </div>

            {loadingSubscriptions ? (
              <p>Loading subscriptions...</p>
            ) : studentSubscriptions.length === 0 ? (
              <p style={{ color: "var(--text-secondary)", marginBottom: "1rem" }}>No active subscriptions for this student.</p>
            ) : (
              <ul style={{ listStyle: "none", padding: 0, marginBottom: "1.5rem" }}>
                {studentSubscriptions.map(sub => (
                  <li key={sub.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "0.75rem", background: "rgba(255,255,255,0.05)", borderRadius: "8px", marginBottom: "0.5rem" }}>
                    <div>
                      <span style={{ fontWeight: 600 }}>{sub.name}</span>
                    </div>
                    <button
                      className={styles.revokeBtn}
                      // MODULE 4 FIX: Pass package ID + name for reliable revoke
                      onClick={() => handleRevokeSpecificAccess(selectedStudentId, sub.id, sub.name)}
                      style={{ padding: "0.3rem 0.85rem", fontSize: "0.85rem" }}
                    >
                      🗑️ Revoke
                    </button>
                  </li>
                ))}
              </ul>
            )}

            {/* Grant New Package */}
            <div style={{ marginTop: "2rem", paddingTop: "1.5rem", borderTop: "1px solid rgba(255,255,255,0.1)" }}>
              <h3 style={{ marginBottom: "1rem" }}>➕ Grant New Package</h3>
              <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", flexWrap: "wrap" }}>
                <select
                  value={grantCategory}
                  onChange={(e) => setGrantCategory(e.target.value)}
                  style={{ padding: "0.5rem", borderRadius: "4px", border: "1px solid #ccc", color: "black" }}
                >
                  <option value="10th Class">10th Class</option>
                  <option value="IMO Test">IMO Test</option>
                  <option value="Book Library">Book Library</option>
                  <option value="Chess">Chess Tutor</option>
                </select>

                {grantCategory === "10th Class" && (
                  <select value={grantSubject} onChange={(e) => setGrantSubject(e.target.value)} style={{ padding: "0.5rem", borderRadius: "4px", border: "1px solid #ccc", color: "black" }}>
                    {["Maths", "Marathi", "Computers", "Science", "SST", "English"].map(s => (<option key={s} value={s}>{s}</option>))}
                  </select>
                )}

                {grantCategory === "IMO Test" && (
                  <select value={grantGrade} onChange={(e) => setGrantGrade(e.target.value)} style={{ padding: "0.5rem", borderRadius: "4px", border: "1px solid #ccc", color: "black" }}>
                    {[...Array(10)].map((_, i) => (<option key={i} value={`Grade ${i + 1}`}>Grade {i + 1}</option>))}
                  </select>
                )}

                <button
                  className={styles.grantBtn}
                  onClick={() => handleGrantAccess(selectedStudentId)}
                >
                  ✅ Grant Package
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Parent-Student Connections */}
      <div className={`glass-panel ${styles.section}`} style={{ marginTop: "2rem" }}>
        <h2 className={styles.sectionTitle}>🔗 Parent-Student Connections</h2>
        <div style={{ display: "flex", gap: "1rem", marginBottom: "1rem", flexWrap: "wrap" }}>
          <select value={selectedParentId} onChange={(e) => setSelectedParentId(e.target.value)} style={{ padding: "0.5rem", borderRadius: "4px", border: "1px solid #ccc", flex: "1 1 200px", color: "black" }}>
            <option value="">-- Select Parent --</option>
            {parents.map(p => <option key={p.id} value={p.id}>{p.full_name || p.name || p.email || p.id.substring(0,8)}</option>)}
          </select>
          <select value={connectionStudentId} onChange={(e) => setConnectionStudentId(e.target.value)} style={{ padding: "0.5rem", borderRadius: "4px", border: "1px solid #ccc", flex: "1 1 200px", color: "black" }}>
            <option value="">-- Select Student --</option>
            {students.map(s => <option key={s.id} value={s.id}>{s.full_name || s.name || s.email || s.id.substring(0,8)}</option>)}
          </select>
          <button className={styles.grantBtn} onClick={handleAddConnection} disabled={!selectedParentId || !connectionStudentId}>
            Assign Connection
          </button>
        </div>
        
        {selectedParentId && (
          <div style={{ marginTop: "1rem" }}>
            <h3 style={{ marginBottom: "0.5rem", fontSize: "1rem" }}>Assigned Students:</h3>
            <ul style={{ listStyle: "none", padding: 0 }}>
              {(parentConnections[selectedParentId] || []).map(sid => {
                const stu = students.find(s => s.id === sid);
                return (
                  <li key={sid} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "0.5rem", background: "rgba(255,255,255,0.05)", borderRadius: "8px", marginBottom: "0.5rem" }}>
                    <span>{stu ? (stu.full_name || stu.name || stu.email) : sid}</span>
                    <button onClick={() => handleRemoveConnection(selectedParentId, sid)} className={styles.revokeBtn} style={{ padding: "0.2rem 0.5rem", fontSize: "0.8rem" }}>Revoke</button>
                  </li>
                );
              })}
              {(parentConnections[selectedParentId] || []).length === 0 && <p style={{ color: "var(--text-secondary)" }}>No students assigned to this parent yet.</p>}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Exported page — ADMIN role only
// ---------------------------------------------------------------------------
export default function AdminPortal() {
  return (
    <AuthGuard requiredRole="ADMIN">
      <AdminPortalContent />
    </AuthGuard>
  );
}
