import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import type { ChatMessage } from "@/types/api";

export interface ChatState {
  messages: ChatMessage[];
  loading: boolean;
  error: string | null;
  currentModel: string;
}

const initialState: ChatState = {
  messages: [],
  loading: false,
  error: null,
  currentModel: "gpt-4",
};

const chatSlice = createSlice({
  name: "chat",
  initialState,
  reducers: {
    addMessage: (state, action: PayloadAction<ChatMessage>) => {
      state.messages.push(action.payload);
    },
    setMessages: (state, action: PayloadAction<ChatMessage[]>) => {
      state.messages = action.payload;
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
    setCurrentModel: (state, action: PayloadAction<string>) => {
      state.currentModel = action.payload;
    },
    clearMessages: (state) => {
      state.messages = [];
    },
  },
});

export const { addMessage, setMessages, setLoading, setError, setCurrentModel, clearMessages } = chatSlice.actions;
export default chatSlice.reducer;
