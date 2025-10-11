const { queryRef, executeQuery, mutationRef, executeMutation, validateArgs } = require('firebase/data-connect');

const connectorConfig = {
  connector: 'example',
  service: 'frontend',
  location: 'europe-west1'
};
exports.connectorConfig = connectorConfig;

const createUserRef = (dcOrVars, vars) => {
  const { dc: dcInstance, vars: inputVars} = validateArgs(connectorConfig, dcOrVars, vars, true);
  dcInstance._useGeneratedSdk();
  return mutationRef(dcInstance, 'CreateUser', inputVars);
}
createUserRef.operationName = 'CreateUser';
exports.createUserRef = createUserRef;

exports.createUser = function createUser(dcOrVars, vars) {
  return executeMutation(createUserRef(dcOrVars, vars));
};

const getNoteProjectsByUserRef = (dc) => {
  const { dc: dcInstance} = validateArgs(connectorConfig, dc, undefined);
  dcInstance._useGeneratedSdk();
  return queryRef(dcInstance, 'GetNoteProjectsByUser');
}
getNoteProjectsByUserRef.operationName = 'GetNoteProjectsByUser';
exports.getNoteProjectsByUserRef = getNoteProjectsByUserRef;

exports.getNoteProjectsByUser = function getNoteProjectsByUser(dc) {
  return executeQuery(getNoteProjectsByUserRef(dc));
};

const createNoteImageRef = (dcOrVars, vars) => {
  const { dc: dcInstance, vars: inputVars} = validateArgs(connectorConfig, dcOrVars, vars, true);
  dcInstance._useGeneratedSdk();
  return mutationRef(dcInstance, 'CreateNoteImage', inputVars);
}
createNoteImageRef.operationName = 'CreateNoteImage';
exports.createNoteImageRef = createNoteImageRef;

exports.createNoteImage = function createNoteImage(dcOrVars, vars) {
  return executeMutation(createNoteImageRef(dcOrVars, vars));
};

const createTranscriptionRef = (dcOrVars, vars) => {
  const { dc: dcInstance, vars: inputVars} = validateArgs(connectorConfig, dcOrVars, vars, true);
  dcInstance._useGeneratedSdk();
  return mutationRef(dcInstance, 'CreateTranscription', inputVars);
}
createTranscriptionRef.operationName = 'CreateTranscription';
exports.createTranscriptionRef = createTranscriptionRef;

exports.createTranscription = function createTranscription(dcOrVars, vars) {
  return executeMutation(createTranscriptionRef(dcOrVars, vars));
};
