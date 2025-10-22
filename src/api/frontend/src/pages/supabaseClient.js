import { createClient } from "@supabase/supabase-js";

console.log("Supabase URL:", "https://awdsavchsxfwtyprtsah.supabase.co");
console.log("Supabase Key:", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF3ZHNhdmNoc3hmd3R5cHJ0c2FoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjA2MzI4ODEsImV4cCI6MjA3NjIwODg4MX0.YYdkQxdG9arBERDXMUdskax8iXOrXt6lBLrFPNsLwsA");
const supabaseUrl = "https://awdsavchsxfwtyprtsah.supabase.co";
const supabaseAnonKey = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF3ZHNhdmNoc3hmd3R5cHJ0c2FoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjA2MzI4ODEsImV4cCI6MjA3NjIwODg4MX0.YYdkQxdG9arBERDXMUdskax8iXOrXt6lBLrFPNsLwsA";


export const supabase = createClient(supabaseUrl, supabaseAnonKey);