// User types
export interface User {
  id: string;
  email: string;
  name: string;
  created_at: string;
  updated_at: string;
}

// Project types
export interface Project {
  id: string;
  name: string;
  description?: string;
  objectives?: string;
  keywords?: string[];
  status?: 'active' | 'archived';
  created_at: string;
  updated_at: string;
  owner_id: string;
  document_count?: number;
  total_chunks?: number;
  total_entities?: number;
  total_relations?: number;
  total_messages?: number;
  storage_used?: number;
  last_accessed?: string;
}

// Document types
export interface Document {
  id: string;
  project_id: string;
  filename: string;
  file_type: string;
  file_size: number;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  error_message?: string;
  page_count?: number;
  word_count?: number;
  created_at: string;
  updated_at: string;
}

// Chunk types
export interface Chunk {
  id: string;
  document_id: string;
  content: string;
  chunk_index: number;
  start_page?: number;
  end_page?: number;
  metadata?: Record<string, any>;
}

// Conversation types
export interface Conversation {
  id: string;
  project_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  sources?: Source[];
  created_at: string;
}

export interface Source {
  chunk_id: string;
  document_id: string;
  document_name: string;
  page_number?: number;
  relevance_score: number;
  content_preview: string;
}

// Knowledge Graph types
export interface KnowledgeGraphNode {
  id: string;
  label: string;
  type: 'concept' | 'entity' | 'document' | 'topic';
  properties: Record<string, any>;
}

export interface KnowledgeGraphEdge {
  id: string;
  source: string;
  target: string;
  type: string;
  weight?: number;
}

export interface KnowledgeGraph {
  nodes: KnowledgeGraphNode[];
  edges: KnowledgeGraphEdge[];
}

// API Response types
export interface ApiResponse<T> {
  data: T;
  message?: string;
  error?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}