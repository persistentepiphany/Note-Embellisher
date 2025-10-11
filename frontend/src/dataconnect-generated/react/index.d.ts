import { CreateUserData, CreateUserVariables, GetNoteProjectsByUserData, CreateNoteImageData, CreateNoteImageVariables, CreateTranscriptionData, CreateTranscriptionVariables } from '../';
import { UseDataConnectQueryResult, useDataConnectQueryOptions, UseDataConnectMutationResult, useDataConnectMutationOptions} from '@tanstack-query-firebase/react/data-connect';
import { UseQueryResult, UseMutationResult} from '@tanstack/react-query';
import { DataConnect } from 'firebase/data-connect';
import { FirebaseError } from 'firebase/app';


export function useCreateUser(options?: useDataConnectMutationOptions<CreateUserData, FirebaseError, CreateUserVariables>): UseDataConnectMutationResult<CreateUserData, CreateUserVariables>;
export function useCreateUser(dc: DataConnect, options?: useDataConnectMutationOptions<CreateUserData, FirebaseError, CreateUserVariables>): UseDataConnectMutationResult<CreateUserData, CreateUserVariables>;

export function useGetNoteProjectsByUser(options?: useDataConnectQueryOptions<GetNoteProjectsByUserData>): UseDataConnectQueryResult<GetNoteProjectsByUserData, undefined>;
export function useGetNoteProjectsByUser(dc: DataConnect, options?: useDataConnectQueryOptions<GetNoteProjectsByUserData>): UseDataConnectQueryResult<GetNoteProjectsByUserData, undefined>;

export function useCreateNoteImage(options?: useDataConnectMutationOptions<CreateNoteImageData, FirebaseError, CreateNoteImageVariables>): UseDataConnectMutationResult<CreateNoteImageData, CreateNoteImageVariables>;
export function useCreateNoteImage(dc: DataConnect, options?: useDataConnectMutationOptions<CreateNoteImageData, FirebaseError, CreateNoteImageVariables>): UseDataConnectMutationResult<CreateNoteImageData, CreateNoteImageVariables>;

export function useCreateTranscription(options?: useDataConnectMutationOptions<CreateTranscriptionData, FirebaseError, CreateTranscriptionVariables>): UseDataConnectMutationResult<CreateTranscriptionData, CreateTranscriptionVariables>;
export function useCreateTranscription(dc: DataConnect, options?: useDataConnectMutationOptions<CreateTranscriptionData, FirebaseError, CreateTranscriptionVariables>): UseDataConnectMutationResult<CreateTranscriptionData, CreateTranscriptionVariables>;
