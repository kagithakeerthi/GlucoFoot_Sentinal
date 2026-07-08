import { useEffect, useState } from 'react';
import { Link, Navigate, Route, Routes, useLocation, useNavigate } from 'react-router-dom';
import axios from 'axios';

const API_BASE = 'http://localhost:5000/api';

function App() {
  const [user, setUser] = useState(null);
  const [patients, setPatients] = useState([]);
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    axios.get(`${API_BASE}/auth/me`, { withCredentials: true }).then((res) => setUser(res.data.user)).catch(() => setUser(null));
  }, []);

  useEffect(() => {
    if (user) {
      loadPatients();
      loadReports();
    }
  }, [user]);

  const loadPatients = async () => {
    try {
      const res = await axios.get(`${API_BASE}/patients`, { withCredentials: true });
      setPatients(res.data.patients || []);
    } catch (error) {
      console.error(error);
    }
  };

  const loadReports = async () => {
    try {
      const res = await axios.get(`${API_BASE}/reports`, { withCredentials: true });
      setReports(res.data.reports || []);
    } catch (error) {
      console.error(error);
    }
  };

  const handleLogout = async () => {
    await axios.post(`${API_BASE}/auth/logout`, {}, { withCredentials: true });
    setUser(null);
    navigate('/');
  };

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">GlucoFoot Sentinel</div>
        <nav className="nav-links">
          <Link to="/">Home</Link>
          {user ? <Link to="/dashboard">Dashboard</Link> : <Link to="/login">Login</Link>}
          {user ? <button className="ghost-btn" onClick={handleLogout}>Logout</button> : <Link to="/register" className="btn">Register</Link>}
        </nav>
      </header>

      <Routes>
        <Route path="/" element={<LandingPage user={user} />} />
        <Route path="/login" element={<AuthPage mode="login" onAuth={setUser} />} />
        <Route path="/register" element={<AuthPage mode="register" onAuth={setUser} />} />
        <Route path="/dashboard" element={user ? <Dashboard user={user} patients={patients} reports={reports} loading={loading} setLoading={setLoading} /> : <Navigate to="/login" replace />} />
      </Routes>
    </div>
  );
}

function LandingPage({ user }) {
  const primaryLink = user ? '/dashboard#patient-form' : '/register';
  const secondaryLink = user ? '/dashboard#prediction-result' : '/login';
  const featureCards = [
    { icon: '🧾', title: 'Create a patient profile', text: 'Add patient details, symptoms, and medical context in a guided experience.', link: user ? '/dashboard#patient-form' : '/register' },
    { icon: '📸', title: 'Uploaded images', text: 'Review your previously uploaded left and right foot images in one place.', link: user ? '/dashboard#uploaded-images' : '/register' },
    { icon: '🧠', title: 'See screening results', text: 'Review your previous predictions, confidence, and recommendations instantly.', link: user ? '/dashboard#previous-results' : '/register' },
  ];
  return (
    <main className="hero">
      <section className="hero-card">
        <div>
          <p className="eyebrow">Modern AI screening workspace</p>
          <h1>Fast, calm, and intelligent foot screening for diabetic care.</h1>
          <p>GlucoFoot Sentinel gives your team a beautiful, interactive flow to review patient details, symptoms, images, and screening outcomes in one place.</p>
          <div className="hero-actions">
            <Link className="btn" to={primaryLink}>{user ? 'Open Dashboard' : 'Get Started'}</Link>
            <Link className="ghost-btn" to={secondaryLink}>{user ? 'Continue Session' : 'Sign In'}</Link>
          </div>
        </div>
        <div className="hero-panel">
          <div className="mini-pill">Live demo experience</div>
          <h3>What the flow looks like</h3>
          <div className="step-list">
            <div className="step-item"><span>1</span><p>{user ? 'Open the dashboard and create a profile' : 'Register and open the dashboard'}</p></div>
            <div className="step-item"><span>2</span><p>Enter medical details and symptoms</p></div>
            <div className="step-item"><span>3</span><p>Upload foot images and run screening</p></div>
          </div>
        </div>
      </section>

      <section className="card-grid">
        {featureCards.map((card) => (
          <FeatureCard key={card.title} icon={card.icon} title={card.title} text={card.text} link={card.link} />
        ))}
      </section>

      <section className="highlight-section">
        <div className="highlight-card">
          <h3>Designed for a polished hackathon demo</h3>
          <p>Every section now has a more purposeful layout, better spacing, and smoother interactions so the experience feels premium and easy to present.</p>
        </div>
      </section>
    </main>
  );
}

function FeatureCard({ icon, title, text, link }) {
  return (
    <Link to={link} className="feature-card">
      <div className="feature-icon">{icon}</div>
      <h3>{title}</h3>
      <p>{text}</p>
      <span className="feature-link">Open now →</span>
    </Link>
  );
}

function AuthPage({ mode, onAuth }) {
  const [form, setForm] = useState({ username: '', email: '', password: '' });
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      const endpoint = mode === 'register' ? '/auth/register' : '/auth/login';
      const res = await axios.post(`${API_BASE}${endpoint}`, form, { withCredentials: true });
      onAuth(res.data.user);
      navigate('/dashboard');
    } catch (err) {
      if (err.response) {
        const status = err.response.status;
        const msg = err.response.data?.error || err.response.data?.message || 'Request failed';
        if (status === 400) {
          setError(msg);
        } else if (status === 401) {
          setError('Invalid credentials or user not registered');
        } else {
          setError(msg);
        }
      } else {
        setError('Network error — could not reach server');
      }
    }
  };

  return (
    <div className="auth-card">
      <div className="auth-glow" />
      <h2>{mode === 'register' ? 'Create an account' : 'Welcome back'}</h2>
      <p className="subtle-text">Secure access to your screening workspace.</p>
      <form onSubmit={handleSubmit} className="stacked-form">
        {mode === 'register' && (
          <input placeholder="Username" value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} />
        )}
        <input type="email" placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
        <input type="password" placeholder="Password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
        <button className="btn" type="submit">{mode === 'register' ? 'Register' : 'Login'}</button>
      </form>
      {error && <p className="error">{error}</p>}
    </div>
  );
}

function Dashboard({ user, patients, reports, loading, setLoading }) {
  const location = useLocation();
  const [patientForm, setPatientForm] = useState({
    name: '', age: '', ageUnit: 'years', gender: 'Male', weight: '', weightUnit: 'kg', height: '', heightUnit: 'cm', diabetes_duration: '', diabetesUnit: 'years', hba1c: '', fasting_blood_sugar: '', random_blood_sugar: '', current_medication: '',
    redness: false, swelling: false, pain: false, fever: false, numbness: false, cracks: false, previous_foot_ulcer: false, previous_cellulitis: false,
  });
  const [formError, setFormError] = useState('');
  const [activeUpload, setActiveUpload] = useState('left');
  const [leftImage, setLeftImage] = useState(null);
  const [rightImage, setRightImage] = useState(null);
  const [result, setResult] = useState(null);
  const [search, setSearch] = useState('');

  useEffect(() => {
    const hash = location.hash?.slice(1);
    if (!hash) {
      window.scrollTo({ top: 0, behavior: 'smooth' });
      return;
    }
    const target = document.getElementById(hash);
    if (target) {
      setTimeout(() => target.scrollIntoView({ behavior: 'smooth', block: 'start' }), 120);
    }
  }, [location.hash]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    // prevent negative numbers for numeric fields
    let next = value;
    if (type === 'number' && value !== '') {
      const num = Number(value);
      next = String(Number.isNaN(num) ? '' : Math.max(0, num));
    }
    setPatientForm((prev) => ({ ...prev, [name]: type === 'checkbox' ? checked : next }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setFormError('');
    setLoading(true);
    // Normalize units: weight -> kg, height -> cm
    const payload = { ...patientForm };
    // validate required fields
    if (!payload.name || !payload.name.trim()) {
      setFormError('Patient name is required');
      setLoading(false);
      return;
    }
    if (payload.age === '' || Number(payload.age) <= 0) {
      setFormError('Please enter a valid non-negative age');
      setLoading(false);
      return;
    }
    const rawWeight = parseFloat(payload.weight || 0) || 0;
    if (payload.weightUnit === 'g') {
      payload.weight = (rawWeight / 1000).toString();
    } else {
      // assume kg
      payload.weight = rawWeight.toString();
    }
    const rawHeight = parseFloat(payload.height || 0) || 0;
    if (payload.heightUnit === 'm') {
      payload.height = (rawHeight * 100).toString(); // convert meters to cm
    } else {
      // assume cm
      payload.height = rawHeight.toString();
    }
    // convert age units: months -> years (float), years stays
    const rawAge = parseFloat(payload.age || 0) || 0;
    if (payload.ageUnit === 'months') {
      payload.age = (rawAge / 12).toFixed(2).toString();
    } else {
      payload.age = rawAge.toString();
    }
    // convert diabetes duration units to years
    const rawDuration = parseFloat(payload.diabetes_duration || 0) || 0;
    if (payload.diabetesUnit === 'days') {
      payload.diabetes_duration = (rawDuration / 365).toFixed(2).toString();
    } else if (payload.diabetesUnit === 'months') {
      payload.diabetes_duration = (rawDuration / 12).toFixed(2).toString();
    } else {
      payload.diabetes_duration = rawDuration.toString();
    }

    const formData = new FormData();
    Object.entries(payload).forEach(([key, value]) => {
      if (['weightUnit', 'heightUnit', 'ageUnit', 'diabetesUnit'].includes(key)) return;
      formData.append(key, value);
    });
    if (leftImage) formData.append('left_image', leftImage);
    if (rightImage) formData.append('right_image', rightImage);
    try {
      const res = await axios.post(`${API_BASE}/predict`, formData, { withCredentials: true, headers: { 'Content-Type': 'multipart/form-data' } });
      setResult(res.data);
    } catch (error) {
      console.error(error);
      // show user-friendly message in UI
      if (error.response) {
        const status = error.response.status;
        const msg = error.response.data?.error || error.response.data?.message || 'Request failed';
        setResult({ error: status === 401 ? 'Invalid credentials or not registered' : msg });
      } else {
        setResult({ error: 'Network error — could not reach server' });
      }
    } finally {
      setLoading(false);
    }
  };

  const filteredPatients = patients.filter((patient) => patient.name?.toLowerCase().includes(search.toLowerCase()));

  return (
    <main className="dashboard-grid">
      <section className="card wide hero-intro">
        <div>
          <p className="eyebrow">Interactive screening workspace</p>
          <h2>Welcome, {user?.username || 'care team'}</h2>
          <p>Use this workspace to document patient details, upload foot images, and generate a screening result with a modern clinical feel.</p>
        </div>
        <div className="status-card">Fast · Secure · Demo-ready</div>
      </section>

      <section id="patient-form" className="card">
        <h3>Patient Screening Form</h3>
        <form onSubmit={handleSubmit} className="stacked-form">
          <input name="name" placeholder="Patient Name" onChange={handleChange} value={patientForm.name} required />
          <div className="input-row">
            <div>
              <label className="field-label">Age <span className="required">*</span></label>
              <div className="field-with-unit right-unit">
                <input name="age" type="number" placeholder="Age" onChange={handleChange} value={patientForm.age} min="0" required />
                <select name="ageUnit" value={patientForm.ageUnit} onChange={handleChange} className="unit-select">
                  <option value="years">yrs</option>
                  <option value="months">mos</option>
                </select>
              </div>
            </div>
            <div>
              <label className="field-label">Gender <span className="required">*</span></label>
              <select name="gender" value={patientForm.gender} onChange={handleChange}>
                <option value="Male">Male</option>
                <option value="Female">Female</option>
                <option value="Custom">Custom</option>
              </select>
            </div>
          </div>
          <div className="input-row">
            <div>
              <label className="field-label">Weight <span className="required">*</span></label>
              <div className="field-with-unit right-unit">
                <input name="weight" type="number" placeholder="Weight" onChange={handleChange} value={patientForm.weight} min="0" required />
                <select name="weightUnit" value={patientForm.weightUnit} onChange={handleChange} className="unit-select">
                  <option value="kg">kg</option>
                  <option value="g">g</option>
                  <option value="lb">lb</option>
                </select>
              </div>
            </div>
            <div>
              <label className="field-label">Height <span className="required">*</span></label>
              <div className="field-with-unit right-unit">
                <input name="height" type="number" placeholder="Height" onChange={handleChange} value={patientForm.height} min="0" required />
                <select name="heightUnit" value={patientForm.heightUnit} onChange={handleChange} className="unit-select">
                  <option value="cm">cm</option>
                  <option value="m">m</option>
                  <option value="in">in</option>
                </select>
              </div>
            </div>
          </div>
          <div>
            <label className="field-label">Diabetes Duration</label>
            <div className="field-with-unit right-unit">
              <input name="diabetes_duration" type="number" placeholder="Diabetes Duration" onChange={handleChange} value={patientForm.diabetes_duration} />
              <select name="diabetesUnit" value={patientForm.diabetesUnit} onChange={handleChange} className="unit-select">
                <option value="years">yrs</option>
                <option value="months">mos</option>
                <option value="days">days</option>
              </select>
            </div>
          </div>
          <input name="hba1c" type="number" step="0.1" placeholder="HbA1c" onChange={handleChange} value={patientForm.hba1c} />
          <div className="input-row">
            <input name="fasting_blood_sugar" type="number" placeholder="Fasting Blood Sugar" onChange={handleChange} value={patientForm.fasting_blood_sugar} />
            <input name="random_blood_sugar" type="number" placeholder="Random Blood Sugar" onChange={handleChange} value={patientForm.random_blood_sugar} />
          </div>
          <input name="current_medication" placeholder="Current Medication" onChange={handleChange} value={patientForm.current_medication} />

          <div className="checkbox-grid">
            {['redness', 'swelling', 'pain', 'fever', 'numbness', 'cracks', 'previous_foot_ulcer', 'previous_cellulitis'].map((key) => (
              <label key={key} className="chip">
                <input type="checkbox" name={key} checked={patientForm[key]} onChange={handleChange} /> {key.replace(/_/g, ' ')}
              </label>
            ))}
          </div>

          <div id="upload-area" className="upload-row">
            <button type="button" className={`upload-card ${activeUpload === 'left' ? 'active' : ''}`} onClick={() => setActiveUpload('left')}>
              <span>🦶</span>
              <strong>Left Foot Image</strong>
              <small>{leftImage ? leftImage.name : 'Upload image'}</small>
            </button>
            <button type="button" className={`upload-card ${activeUpload === 'right' ? 'active' : ''}`} onClick={() => setActiveUpload('right')}>
              <span>🦶</span>
              <strong>Right Foot Image</strong>
              <small>{rightImage ? rightImage.name : 'Upload image'}</small>
            </button>
          </div>

          <label className="file-picker">
            <span>{activeUpload === 'left' ? 'Choose left foot image' : 'Choose right foot image'}</span>
            <input type="file" accept="image/*" onChange={(e) => activeUpload === 'left' ? setLeftImage(e.target.files[0]) : setRightImage(e.target.files[0])} />
          </label>

          {formError && <p className="error">{formError}</p>}
          <button className="btn" type="submit">Run Screening</button>
        </form>
      </section>

      <section id="prediction-result" className="card">
        <h3>Prediction Result</h3>
        {loading ? <div className="loader">Analyzing patient data...</div> : result ? (
          result.error ? (
            <div className="result-box">
              <p className="error">{result.error}</p>
            </div>
          ) : (
            <div className="result-box">
              <p><strong>Prediction:</strong> {result.prediction.prediction}</p>
              <p><strong>Confidence:</strong> {result.prediction.confidence_score}</p>
              <p><strong>Risk Level:</strong> {result.prediction.risk_level}</p>
              <p><strong>Recommendation:</strong> {result.prediction.recommendation}</p>
              {result.report_file && <a className="btn inline" href={`http://localhost:5000/api/reports/${result.prediction_id}/download`} target="_blank" rel="noreferrer">Download PDF</a>}
            </div>
          )
        ) : <p className="subtle-text">No result yet. Submit the form to see predictions.</p>}
      </section>

      <section id="uploaded-images" className="card wide">
        <h3>Previously Uploaded Images</h3>
        <div className="record-list">
          {patients.length === 0 ? <p className="subtle-text">No uploaded images yet.</p> : patients.map((patient) => (
            <div className="record-item" key={patient.id}>
              <div>
                <strong>{patient.name || 'Unnamed patient'}</strong>
                <div className="subtle-text">{patient.age} yrs · {patient.gender}</div>
              </div>
              <div className="image-preview-list">
                {patient.images?.filter(Boolean).length ? patient.images.map((image, index) => (
                  <a key={`${patient.id}-${index}`} href={`${API_BASE}/images/${image.left_image || image.right_image || ''}`} target="_blank" rel="noreferrer" className="image-preview-pill">
                    {index === 0 ? 'Left image' : 'Right image'}
                  </a>
                )) : <span className="subtle-text">No images</span>}
              </div>
            </div>
          ))}
        </div>
      </section>

      <section id="previous-results" className="card wide">
        <h3>Previous Predictions</h3>
        <div className="record-list">
          {patients.length === 0 ? <p className="subtle-text">No previous screening results yet.</p> : patients.map((patient) => (
            <div className="record-item" key={patient.id}>
              <div>
                <strong>{patient.name || 'Unnamed patient'}</strong>
                <div className="subtle-text">{patient.age} yrs · {patient.gender}</div>
              </div>
              <div className="result-stack">
                {patient.predictions?.length ? patient.predictions.map((prediction) => (
                  <div key={prediction.id} className="prediction-pill">
                    <span>{prediction.prediction}</span>
                    <small>{prediction.risk_level}</small>
                  </div>
                )) : <span className="subtle-text">No predictions</span>}
              </div>
            </div>
          ))}
        </div>
      </section>

      <section id="patient-records" className="card wide">
        <h3>Patient Records</h3>
        <input placeholder="Search patients" value={search} onChange={(e) => setSearch(e.target.value)} />
        <div className="record-list">
          {filteredPatients.map((patient) => (
            <div className="record-item" key={patient.id}>
              <strong>{patient.name}</strong>
              <span>{patient.age} yrs · {patient.gender}</span>
              <span>{patient.predictions?.[0]?.prediction || 'Pending'}</span>
            </div>
          ))}
        </div>
      </section>

      <section id="recent-reports" className="card wide">
        <h3>Recent Reports</h3>
        <div className="record-list">
          {reports.map((report) => (
            <div className="record-item" key={report.id}>
              <strong>{report.file_name}</strong>
              <span>{new Date(report.created_at).toLocaleString()}</span>
              <a href={`http://localhost:5000/api/reports/${report.id}/download`} target="_blank" rel="noreferrer">Download</a>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}

export default App;
