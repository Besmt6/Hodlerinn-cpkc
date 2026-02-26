import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import GuestPortal from "@/pages/GuestPortal";
import AdminLogin from "@/pages/AdminLogin";
import AdminDashboard from "@/pages/AdminDashboard";

// Base path for custom domain routing (e.g., hodlerinn.com/cpkc)
const BASENAME = process.env.REACT_APP_BASE_PATH || "";

function App() {
  return (
    <div className="App">
      <BrowserRouter basename={BASENAME}>
        <Routes>
          <Route path="/" element={<GuestPortal />} />
          <Route path="/admin" element={<AdminLogin />} />
          <Route path="/admin/dashboard" element={<AdminDashboard />} />
        </Routes>
      </BrowserRouter>
      <Toaster position="top-right" richColors />
      <div className="noise-overlay" />
    </div>
  );
}

export default App;
