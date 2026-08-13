import { initializeApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";
import { getAuth, GoogleAuthProvider } from "firebase/auth";

const firebaseConfig = {
  apiKey: "AIzaSyAXEzsm21KbFPF4o07GqxjO1mH90Uh24W8",
  authDomain: "neurostore-5b1f0.firebaseapp.com",
  projectId: "neurostore-5b1f0",
  storageBucket: "neurostore-5b1f0.firebasestorage.app",
  messagingSenderId: "899112067022",
  appId: "1:899112067022:web:1dad2d8b07280ebe0fd59f",
  measurementId: "G-YGV6Z2YS6F"
};

const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);
export const auth = getAuth(app);
export const googleProvider = new GoogleAuthProvider();
export default app;