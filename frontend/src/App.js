import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import GuestPortal from "@/pages/GuestPortal";
import AdminLogin from "@/pages/AdminLogin";
import AdminDashboard from "@/pages/AdminDashboard";
import BookNow from "@/pages/BookNow";

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<GuestPortal />} />
          <Route path="/admin" element={<AdminLogin />} />
          <Route path="/admin/dashboard" element={<AdminDashboard />} />
          <Route path="/book" element={<BookNow />} />
        </Routes>
      </BrowserRouter>
      <Toaster position="top-right" richColors />
      <div className="noise-overlay" />
    </div>
  );
}

export default App;
