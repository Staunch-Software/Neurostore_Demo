// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyAXEzsm21KbFPF4o07GqxjO1mH90Uh24W8",
  authDomain: "neurostore-5b1f0.firebaseapp.com",
  projectId: "neurostore-5b1f0",
  storageBucket: "neurostore-5b1f0.firebasestorage.app",
  messagingSenderId: "899112067022",
  appId: "1:899112067022:web:1dad2d8b07280ebe0fd59f",
  measurementId: "G-YGV6Z2YS6F"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);
export const googleProvider = new GoogleAuthProvider();
export default app;