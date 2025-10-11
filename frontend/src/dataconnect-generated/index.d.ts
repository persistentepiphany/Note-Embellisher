import { ConnectorConfig, DataConnect, QueryRef, QueryPromise, MutationRef, MutationPromise } from 'firebase/data-connect';

export const connectorConfig: ConnectorConfig;

export type TimestampString = string;
export type UUIDString = string;
export type Int64String = string;
export type DateString = string;




export interface CreateNoteImageData {
  noteImage_insert: NoteImage_Key;
}

export interface CreateNoteImageVariables {
  noteProjectId: UUIDString;
  imageUrl: string;
  originalFilename?: string | null;
  status: string;
}

export interface CreateTranscriptionData {
  transcription_insert: Transcription_Key;
}

export interface CreateTranscriptionVariables {
  noteImageId: UUIDString;
  transcribedText: string;
}

export interface CreateUserData {
  user_insert: User_Key;
}

export interface CreateUserVariables {
  displayName: string;
  email?: string | null;
  photoUrl?: string | null;
}

export interface GetNoteProjectsByUserData {
  noteProjects: ({
    id: UUIDString;
    name: string;
    description?: string | null;
    createdAt: TimestampString;
  } & NoteProject_Key)[];
}

export interface NoteImage_Key {
  id: UUIDString;
  __typename?: 'NoteImage_Key';
}

export interface NoteProject_Key {
  id: UUIDString;
  __typename?: 'NoteProject_Key';
}

export interface Transcription_Key {
  id: UUIDString;
  __typename?: 'Transcription_Key';
}

export interface User_Key {
  id: UUIDString;
  __typename?: 'User_Key';
}

interface CreateUserRef {
  /* Allow users to create refs without passing in DataConnect */
  (vars: CreateUserVariables): MutationRef<CreateUserData, CreateUserVariables>;
  /* Allow users to pass in custom DataConnect instances */
  (dc: DataConnect, vars: CreateUserVariables): MutationRef<CreateUserData, CreateUserVariables>;
  operationName: string;
}
export const createUserRef: CreateUserRef;

export function createUser(vars: CreateUserVariables): MutationPromise<CreateUserData, CreateUserVariables>;
export function createUser(dc: DataConnect, vars: CreateUserVariables): MutationPromise<CreateUserData, CreateUserVariables>;

interface GetNoteProjectsByUserRef {
  /* Allow users to create refs without passing in DataConnect */
  (): QueryRef<GetNoteProjectsByUserData, undefined>;
  /* Allow users to pass in custom DataConnect instances */
  (dc: DataConnect): QueryRef<GetNoteProjectsByUserData, undefined>;
  operationName: string;
}
export const getNoteProjectsByUserRef: GetNoteProjectsByUserRef;

export function getNoteProjectsByUser(): QueryPromise<GetNoteProjectsByUserData, undefined>;
export function getNoteProjectsByUser(dc: DataConnect): QueryPromise<GetNoteProjectsByUserData, undefined>;

interface CreateNoteImageRef {
  /* Allow users to create refs without passing in DataConnect */
  (vars: CreateNoteImageVariables): MutationRef<CreateNoteImageData, CreateNoteImageVariables>;
  /* Allow users to pass in custom DataConnect instances */
  (dc: DataConnect, vars: CreateNoteImageVariables): MutationRef<CreateNoteImageData, CreateNoteImageVariables>;
  operationName: string;
}
export const createNoteImageRef: CreateNoteImageRef;

export function createNoteImage(vars: CreateNoteImageVariables): MutationPromise<CreateNoteImageData, CreateNoteImageVariables>;
export function createNoteImage(dc: DataConnect, vars: CreateNoteImageVariables): MutationPromise<CreateNoteImageData, CreateNoteImageVariables>;

interface CreateTranscriptionRef {
  /* Allow users to create refs without passing in DataConnect */
  (vars: CreateTranscriptionVariables): MutationRef<CreateTranscriptionData, CreateTranscriptionVariables>;
  /* Allow users to pass in custom DataConnect instances */
  (dc: DataConnect, vars: CreateTranscriptionVariables): MutationRef<CreateTranscriptionData, CreateTranscriptionVariables>;
  operationName: string;
}
export const createTranscriptionRef: CreateTranscriptionRef;

export function createTranscription(vars: CreateTranscriptionVariables): MutationPromise<CreateTranscriptionData, CreateTranscriptionVariables>;
export function createTranscription(dc: DataConnect, vars: CreateTranscriptionVariables): MutationPromise<CreateTranscriptionData, CreateTranscriptionVariables>;

