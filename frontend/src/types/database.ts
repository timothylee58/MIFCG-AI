export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[];

export interface Database {
  public: {
    Tables: {
      profiles: {
        Row: {
          id: string;
          email: string;
          full_name: string | null;
          role: "admin" | "analyst" | "viewer";
          organisation: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id: string;
          email: string;
          full_name?: string | null;
          role?: "admin" | "analyst" | "viewer";
          organisation?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: Partial<Database["public"]["Tables"]["profiles"]["Insert"]>;
      };
      compliance_documents: {
        Row: {
          id: string;
          title: string;
          source: "BNM" | "SC" | "PDPA" | "BURSA" | "OTHER";
          file_url: string | null;
          ingested_at: string | null;
          chunk_count: number;
          created_at: string;
        };
        Insert: {
          id?: string;
          title: string;
          source: "BNM" | "SC" | "PDPA" | "BURSA" | "OTHER";
          file_url?: string | null;
          ingested_at?: string | null;
          chunk_count?: number;
          created_at?: string;
        };
        Update: Partial<Database["public"]["Tables"]["compliance_documents"]["Insert"]>;
      };
      document_chunks: {
        Row: {
          id: string;
          document_id: string;
          content: string;
          embedding: number[] | null;
          chunk_index: number;
          metadata: Json;
          created_at: string;
        };
        Insert: {
          id?: string;
          document_id: string;
          content: string;
          embedding?: number[] | null;
          chunk_index: number;
          metadata?: Json;
          created_at?: string;
        };
        Update: Partial<Database["public"]["Tables"]["document_chunks"]["Insert"]>;
      };
      audit_log: {
        Row: {
          id: string;
          user_id: string;
          action: string;
          resource: string;
          metadata: Json;
          created_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          action: string;
          resource: string;
          metadata?: Json;
          created_at?: string;
        };
        Update: never;
      };
    };
    Views: Record<string, never>;
    Functions: {
      match_document_chunks: {
        Args: {
          query_embedding: number[];
          match_threshold: number;
          match_count: number;
          filter_source?: string;
        };
        Returns: {
          id: string;
          document_id: string;
          content: string;
          similarity: number;
          metadata: Json;
        }[];
      };
    };
    Enums: {
      user_role: "admin" | "analyst" | "viewer";
      doc_source: "BNM" | "SC" | "PDPA" | "BURSA" | "OTHER";
    };
  };
}
