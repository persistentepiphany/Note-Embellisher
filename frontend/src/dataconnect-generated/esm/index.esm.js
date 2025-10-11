import { queryRef, executeQuery, mutationRef, executeMutation, validateArgs } from 'firebase/data-connect';

export const connectorConfig = {
  connector: 'example',
  service: 'frontend',
  location: 'europe-west1'
};

export const createUserRef = (dcOrVars, vars) => {
  const { dc: dcInstance, vars: inputVars} = validateArgs(connectorConfig, dcOrVars, vars, true);
  dcInstance._useGeneratedSdk();
  return mutationRef(dcInstance, 'CreateUser', inputVars);
}
createUserRef.operationName = 'CreateUser';

export function createUser(dcOrVars, vars) {
  return executeMutation(createUserRef(dcOrVars, vars));
}

export const getNoteProjectsByUserRef = (dc) => {
  const { dc: dcInstance} = validateArgs(connectorConfig, dc, undefined);
  dcInstance._useGeneratedSdk();
  return queryRef(dcInstance, 'GetNoteProjectsByUser');
}
getNoteProjectsByUserRef.operationName = 'GetNoteProjectsByUser';

export function getNoteProjectsByUser(dc) {
  return executeQuery(getNoteProjectsByUserRef(dc));
}

export const createNoteImageRef = (dcOrVars, vars) => {
  const { dc: dcInstance, vars: inputVars} = validateArgs(connectorConfig, dcOrVars, vars, true);
  dcInstance._useGeneratedSdk();
  return mutationRef(dcInstance, 'CreateNoteImage', inputVars);
}
createNoteImageRef.operationName = 'CreateNoteImage';

export function createNoteImage(dcOrVars, vars) {
  return executeMutation(createNoteImageRef(dcOrVars, vars));
}

export const createTranscriptionRef = (dcOrVars, vars) => {
  const { dc: dcInstance, vars: inputVars} = validateArgs(connectorConfig, dcOrVars, vars, true);
  dcInstance._useGeneratedSdk();
  return mutationRef(dcInstance, 'CreateTranscription', inputVars);
}
createTranscriptionRef.operationName = 'CreateTranscription';

export function createTranscription(dcOrVars, vars) {
  return executeMutation(createTranscriptionRef(dcOrVars, vars));
}

