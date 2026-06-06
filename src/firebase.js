// src/firebase.js
import { initializeApp } from "firebase/app";
import { getAuth, GoogleAuthProvider, FacebookAuthProvider, TwitterAuthProvider, OAuthProvider } from "firebase/auth";

const firebaseConfig = {
  apiKey: "AIzaSyCUpIfPrvC5k-hlZKF2acwcEsubibPJ7hk",
  authDomain: "neurostore-a36a7.firebaseapp.com",
  projectId: "neurostore-a36a7",
  storageBucket: "neurostore-a36a7.firebasestorage.app",
  messagingSenderId: "648543400748",
  appId: "1:648543400748:web:dee2e7fb3458376874b289",
  measurementId: "G-QWM90LQEYH"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);

// Export the Social Providers
export const googleProvider = new GoogleAuthProvider();
googleProvider.setCustomParameters({
  prompt: 'select_account'
});
export const facebookProvider = new FacebookAuthProvider();
export const twitterProvider = new TwitterAuthProvider();
export const appleProvider = new OAuthProvider('apple.com');