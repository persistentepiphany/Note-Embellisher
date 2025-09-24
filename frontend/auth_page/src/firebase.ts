// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";
import { getAuth } from "firebase/auth";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyAJZbEIQHaPPAPE9ntxl1VRoag1KReB-yU",
  authDomain: "note-embellisher-2.firebaseapp.com",
  projectId: "note-embellisher-2",
  storageBucket: "note-embellisher-2.firebasestorage.app",
  messagingSenderId: "113873215178",
  appId: "1:113873215178:web:6077e1a7f322f552201e33",
  measurementId: "G-T0G3516BBB"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);
export const auth = getAuth(app);

