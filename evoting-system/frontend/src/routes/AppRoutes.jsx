import { Routes, Route } from "react-router-dom";
import LandingPage from "../pages/public/LandingPage";
import LoginPage from "../pages/public/LoginPage";
import RegisterPage from "../pages/public/RegisterPage";

import VoterHome from "../pages/voter/VoterHome";
import FaceRegistration from "../pages/voter/FaceRegistration";
import VotingFlow from "../pages/voter/VotingFlow";
import Profile from "../pages/voter/Profile";

import Dashboard from "../pages/admin/Dashboard";
import ElectionManagement from "../pages/admin/ElectionManagement";
import ElectionDetail from "../pages/admin/ElectionDetail";
import VoterRegistration from "../pages/admin/VoterRegistration";
import FraudMonitoring from "../pages/admin/FraudMonitoring";
import BlockchainExplorer from "../pages/admin/BlockchainExplorer";
import AuditLogs from "../pages/admin/AuditLogs";
import Results from "../pages/admin/Results";
import Settings from "../pages/admin/Settings";

import ProtectedRoute from "./ProtectedRoute";

const VOTER_ROLES = ["voter"];
const ADMIN_ROLES = ["super_admin", "election_admin"];

export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      {/* Voter */}
      <Route path="/voter" element={<ProtectedRoute allowedRoles={VOTER_ROLES}><VoterHome /></ProtectedRoute>} />
      <Route path="/voter/register-face" element={<ProtectedRoute allowedRoles={VOTER_ROLES}><FaceRegistration /></ProtectedRoute>} />
      <Route path="/voter/elections/:electionId/vote" element={<ProtectedRoute allowedRoles={VOTER_ROLES}><VotingFlow /></ProtectedRoute>} />
      <Route path="/voter/profile" element={<ProtectedRoute allowedRoles={VOTER_ROLES}><Profile /></ProtectedRoute>} />

      {/* Admin */}
      <Route path="/admin" element={<ProtectedRoute allowedRoles={ADMIN_ROLES}><Dashboard /></ProtectedRoute>} />
      <Route path="/admin/elections" element={<ProtectedRoute allowedRoles={ADMIN_ROLES}><ElectionManagement /></ProtectedRoute>} />
      <Route path="/admin/elections/:electionId" element={<ProtectedRoute allowedRoles={ADMIN_ROLES}><ElectionDetail /></ProtectedRoute>} />
      <Route path="/admin/voters" element={<ProtectedRoute allowedRoles={ADMIN_ROLES}><VoterRegistration /></ProtectedRoute>} />
      <Route path="/admin/fraud" element={<ProtectedRoute allowedRoles={ADMIN_ROLES}><FraudMonitoring /></ProtectedRoute>} />
      <Route path="/admin/blockchain" element={<ProtectedRoute allowedRoles={ADMIN_ROLES}><BlockchainExplorer /></ProtectedRoute>} />
      <Route path="/admin/audit" element={<ProtectedRoute allowedRoles={ADMIN_ROLES}><AuditLogs /></ProtectedRoute>} />
      <Route path="/admin/results" element={<ProtectedRoute allowedRoles={ADMIN_ROLES}><Results /></ProtectedRoute>} />
      <Route path="/admin/settings" element={<ProtectedRoute allowedRoles={ADMIN_ROLES}><Settings /></ProtectedRoute>} />
    </Routes>
  );
}
