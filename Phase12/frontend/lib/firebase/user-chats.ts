/**
 * user_chats/{uid}/sessions/{sessionId} + sub: messages/{messageId}
 * AI 챗봇 세션/메시지 영속화.
 * 스키마: docs/FIREBASE_DB_PLAN.md §3-1
 */
"use client";

import {
  collection,
  doc,
  addDoc,
  setDoc,
  getDocs,
  query,
  orderBy,
  limit,
  serverTimestamp,
  writeBatch,
  type Timestamp,
} from "firebase/firestore";
import { getClientDb } from "./client";

const ROOT = "user_chats";
const SESSIONS = "sessions";
const MESSAGES = "messages";

export interface RemoteChatSession {
  title: string;
  pinned?: boolean;
  messageCount: number;
  createdAt?: Timestamp;
  updatedAt?: Timestamp;
}

export interface RemoteChatMessage {
  role: "user" | "assistant" | "tool";
  content: string;
  parts?: unknown[];
  toolName?: string | null;
  createdAt?: Timestamp;
}

export interface ChatSessionWithId extends RemoteChatSession {
  id: string;
}

function firebaseAvailable(): boolean {
  return Boolean(process.env.NEXT_PUBLIC_FIREBASE_API_KEY);
}

function sessionsRef(uid: string) {
  return collection(getClientDb(), ROOT, uid, SESSIONS);
}
function messagesRef(uid: string, sessionId: string) {
  return collection(getClientDb(), ROOT, uid, SESSIONS, sessionId, MESSAGES);
}

export async function createChatSession(
  uid: string,
  title: string,
): Promise<string | null> {
  if (!firebaseAvailable() || !uid) return null;
  try {
    const ref = await addDoc(sessionsRef(uid), {
      title: title.slice(0, 80),
      pinned: false,
      messageCount: 0,
      createdAt: serverTimestamp(),
      updatedAt: serverTimestamp(),
    });
    return ref.id;
  } catch (err) {
    console.warn("createChatSession failed:", err);
    return null;
  }
}

/**
 * 메시지 일괄 추가 + session 메타 업데이트 (batched).
 * 챗 turn 종료 시 한 번에 저장 (write 비용 ↓).
 */
export async function appendMessages(
  uid: string,
  sessionId: string,
  msgs: RemoteChatMessage[],
): Promise<boolean> {
  if (!firebaseAvailable() || !uid || !sessionId || msgs.length === 0)
    return false;
  try {
    const db = getClientDb();
    const batch = writeBatch(db);
    for (const m of msgs) {
      const ref = doc(messagesRef(uid, sessionId));
      batch.set(ref, { ...m, createdAt: serverTimestamp() });
    }
    batch.set(
      doc(sessionsRef(uid), sessionId),
      {
        messageCount: msgs.length,
        updatedAt: serverTimestamp(),
      },
      { merge: true },
    );
    await batch.commit();
    return true;
  } catch (err) {
    console.warn("appendMessages failed:", err);
    return false;
  }
}

export async function listChatSessions(
  uid: string,
  pageSize: number = 20,
): Promise<ChatSessionWithId[]> {
  if (!firebaseAvailable() || !uid) return [];
  try {
    const q = query(
      sessionsRef(uid),
      orderBy("updatedAt", "desc"),
      limit(pageSize),
    );
    const snap = await getDocs(q);
    return snap.docs.map((d) => ({
      id: d.id,
      ...(d.data() as RemoteChatSession),
    }));
  } catch (err) {
    console.warn("listChatSessions failed:", err);
    return [];
  }
}

export async function listChatMessages(
  uid: string,
  sessionId: string,
  pageSize: number = 200,
): Promise<RemoteChatMessage[]> {
  if (!firebaseAvailable() || !uid || !sessionId) return [];
  try {
    const q = query(
      messagesRef(uid, sessionId),
      orderBy("createdAt", "asc"),
      limit(pageSize),
    );
    const snap = await getDocs(q);
    return snap.docs.map((d) => d.data() as RemoteChatMessage);
  } catch (err) {
    console.warn("listChatMessages failed:", err);
    return [];
  }
}

export async function setSessionPinned(
  uid: string,
  sessionId: string,
  pinned: boolean,
): Promise<boolean> {
  if (!firebaseAvailable() || !uid || !sessionId) return false;
  try {
    await setDoc(
      doc(sessionsRef(uid), sessionId),
      { pinned, updatedAt: serverTimestamp() },
      { merge: true },
    );
    return true;
  } catch (err) {
    console.warn("setSessionPinned failed:", err);
    return false;
  }
}
