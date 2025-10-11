# Generated TypeScript README
This README will guide you through the process of using the generated JavaScript SDK package for the connector `example`. It will also provide examples on how to use your generated SDK to call your Data Connect queries and mutations.

**If you're looking for the `React README`, you can find it at [`dataconnect-generated/react/README.md`](./react/README.md)**

***NOTE:** This README is generated alongside the generated SDK. If you make changes to this file, they will be overwritten when the SDK is regenerated.*

# Table of Contents
- [**Overview**](#generated-javascript-readme)
- [**Accessing the connector**](#accessing-the-connector)
  - [*Connecting to the local Emulator*](#connecting-to-the-local-emulator)
- [**Queries**](#queries)
  - [*GetNoteProjectsByUser*](#getnoteprojectsbyuser)
- [**Mutations**](#mutations)
  - [*CreateUser*](#createuser)
  - [*CreateNoteImage*](#createnoteimage)
  - [*CreateTranscription*](#createtranscription)

# Accessing the connector
A connector is a collection of Queries and Mutations. One SDK is generated for each connector - this SDK is generated for the connector `example`. You can find more information about connectors in the [Data Connect documentation](https://firebase.google.com/docs/data-connect#how-does).

You can use this generated SDK by importing from the package `@dataconnect/generated` as shown below. Both CommonJS and ESM imports are supported.

You can also follow the instructions from the [Data Connect documentation](https://firebase.google.com/docs/data-connect/web-sdk#set-client).

```typescript
import { getDataConnect } from 'firebase/data-connect';
import { connectorConfig } from '@dataconnect/generated';

const dataConnect = getDataConnect(connectorConfig);
```

## Connecting to the local Emulator
By default, the connector will connect to the production service.

To connect to the emulator, you can use the following code.
You can also follow the emulator instructions from the [Data Connect documentation](https://firebase.google.com/docs/data-connect/web-sdk#instrument-clients).

```typescript
import { connectDataConnectEmulator, getDataConnect } from 'firebase/data-connect';
import { connectorConfig } from '@dataconnect/generated';

const dataConnect = getDataConnect(connectorConfig);
connectDataConnectEmulator(dataConnect, 'localhost', 9399);
```

After it's initialized, you can call your Data Connect [queries](#queries) and [mutations](#mutations) from your generated SDK.

# Queries

There are two ways to execute a Data Connect Query using the generated Web SDK:
- Using a Query Reference function, which returns a `QueryRef`
  - The `QueryRef` can be used as an argument to `executeQuery()`, which will execute the Query and return a `QueryPromise`
- Using an action shortcut function, which returns a `QueryPromise`
  - Calling the action shortcut function will execute the Query and return a `QueryPromise`

The following is true for both the action shortcut function and the `QueryRef` function:
- The `QueryPromise` returned will resolve to the result of the Query once it has finished executing
- If the Query accepts arguments, both the action shortcut function and the `QueryRef` function accept a single argument: an object that contains all the required variables (and the optional variables) for the Query
- Both functions can be called with or without passing in a `DataConnect` instance as an argument. If no `DataConnect` argument is passed in, then the generated SDK will call `getDataConnect(connectorConfig)` behind the scenes for you.

Below are examples of how to use the `example` connector's generated functions to execute each query. You can also follow the examples from the [Data Connect documentation](https://firebase.google.com/docs/data-connect/web-sdk#using-queries).

## GetNoteProjectsByUser
You can execute the `GetNoteProjectsByUser` query using the following action shortcut function, or by calling `executeQuery()` after calling the following `QueryRef` function, both of which are defined in [dataconnect-generated/index.d.ts](./index.d.ts):
```typescript
getNoteProjectsByUser(): QueryPromise<GetNoteProjectsByUserData, undefined>;

interface GetNoteProjectsByUserRef {
  ...
  /* Allow users to create refs without passing in DataConnect */
  (): QueryRef<GetNoteProjectsByUserData, undefined>;
}
export const getNoteProjectsByUserRef: GetNoteProjectsByUserRef;
```
You can also pass in a `DataConnect` instance to the action shortcut function or `QueryRef` function.
```typescript
getNoteProjectsByUser(dc: DataConnect): QueryPromise<GetNoteProjectsByUserData, undefined>;

interface GetNoteProjectsByUserRef {
  ...
  (dc: DataConnect): QueryRef<GetNoteProjectsByUserData, undefined>;
}
export const getNoteProjectsByUserRef: GetNoteProjectsByUserRef;
```

If you need the name of the operation without creating a ref, you can retrieve the operation name by calling the `operationName` property on the getNoteProjectsByUserRef:
```typescript
const name = getNoteProjectsByUserRef.operationName;
console.log(name);
```

### Variables
The `GetNoteProjectsByUser` query has no variables.
### Return Type
Recall that executing the `GetNoteProjectsByUser` query returns a `QueryPromise` that resolves to an object with a `data` property.

The `data` property is an object of type `GetNoteProjectsByUserData`, which is defined in [dataconnect-generated/index.d.ts](./index.d.ts). It has the following fields:
```typescript
export interface GetNoteProjectsByUserData {
  noteProjects: ({
    id: UUIDString;
    name: string;
    description?: string | null;
    createdAt: TimestampString;
  } & NoteProject_Key)[];
}
```
### Using `GetNoteProjectsByUser`'s action shortcut function

```typescript
import { getDataConnect } from 'firebase/data-connect';
import { connectorConfig, getNoteProjectsByUser } from '@dataconnect/generated';


// Call the `getNoteProjectsByUser()` function to execute the query.
// You can use the `await` keyword to wait for the promise to resolve.
const { data } = await getNoteProjectsByUser();

// You can also pass in a `DataConnect` instance to the action shortcut function.
const dataConnect = getDataConnect(connectorConfig);
const { data } = await getNoteProjectsByUser(dataConnect);

console.log(data.noteProjects);

// Or, you can use the `Promise` API.
getNoteProjectsByUser().then((response) => {
  const data = response.data;
  console.log(data.noteProjects);
});
```

### Using `GetNoteProjectsByUser`'s `QueryRef` function

```typescript
import { getDataConnect, executeQuery } from 'firebase/data-connect';
import { connectorConfig, getNoteProjectsByUserRef } from '@dataconnect/generated';


// Call the `getNoteProjectsByUserRef()` function to get a reference to the query.
const ref = getNoteProjectsByUserRef();

// You can also pass in a `DataConnect` instance to the `QueryRef` function.
const dataConnect = getDataConnect(connectorConfig);
const ref = getNoteProjectsByUserRef(dataConnect);

// Call `executeQuery()` on the reference to execute the query.
// You can use the `await` keyword to wait for the promise to resolve.
const { data } = await executeQuery(ref);

console.log(data.noteProjects);

// Or, you can use the `Promise` API.
executeQuery(ref).then((response) => {
  const data = response.data;
  console.log(data.noteProjects);
});
```

# Mutations

There are two ways to execute a Data Connect Mutation using the generated Web SDK:
- Using a Mutation Reference function, which returns a `MutationRef`
  - The `MutationRef` can be used as an argument to `executeMutation()`, which will execute the Mutation and return a `MutationPromise`
- Using an action shortcut function, which returns a `MutationPromise`
  - Calling the action shortcut function will execute the Mutation and return a `MutationPromise`

The following is true for both the action shortcut function and the `MutationRef` function:
- The `MutationPromise` returned will resolve to the result of the Mutation once it has finished executing
- If the Mutation accepts arguments, both the action shortcut function and the `MutationRef` function accept a single argument: an object that contains all the required variables (and the optional variables) for the Mutation
- Both functions can be called with or without passing in a `DataConnect` instance as an argument. If no `DataConnect` argument is passed in, then the generated SDK will call `getDataConnect(connectorConfig)` behind the scenes for you.

Below are examples of how to use the `example` connector's generated functions to execute each mutation. You can also follow the examples from the [Data Connect documentation](https://firebase.google.com/docs/data-connect/web-sdk#using-mutations).

## CreateUser
You can execute the `CreateUser` mutation using the following action shortcut function, or by calling `executeMutation()` after calling the following `MutationRef` function, both of which are defined in [dataconnect-generated/index.d.ts](./index.d.ts):
```typescript
createUser(vars: CreateUserVariables): MutationPromise<CreateUserData, CreateUserVariables>;

interface CreateUserRef {
  ...
  /* Allow users to create refs without passing in DataConnect */
  (vars: CreateUserVariables): MutationRef<CreateUserData, CreateUserVariables>;
}
export const createUserRef: CreateUserRef;
```
You can also pass in a `DataConnect` instance to the action shortcut function or `MutationRef` function.
```typescript
createUser(dc: DataConnect, vars: CreateUserVariables): MutationPromise<CreateUserData, CreateUserVariables>;

interface CreateUserRef {
  ...
  (dc: DataConnect, vars: CreateUserVariables): MutationRef<CreateUserData, CreateUserVariables>;
}
export const createUserRef: CreateUserRef;
```

If you need the name of the operation without creating a ref, you can retrieve the operation name by calling the `operationName` property on the createUserRef:
```typescript
const name = createUserRef.operationName;
console.log(name);
```

### Variables
The `CreateUser` mutation requires an argument of type `CreateUserVariables`, which is defined in [dataconnect-generated/index.d.ts](./index.d.ts). It has the following fields:

```typescript
export interface CreateUserVariables {
  displayName: string;
  email?: string | null;
  photoUrl?: string | null;
}
```
### Return Type
Recall that executing the `CreateUser` mutation returns a `MutationPromise` that resolves to an object with a `data` property.

The `data` property is an object of type `CreateUserData`, which is defined in [dataconnect-generated/index.d.ts](./index.d.ts). It has the following fields:
```typescript
export interface CreateUserData {
  user_insert: User_Key;
}
```
### Using `CreateUser`'s action shortcut function

```typescript
import { getDataConnect } from 'firebase/data-connect';
import { connectorConfig, createUser, CreateUserVariables } from '@dataconnect/generated';

// The `CreateUser` mutation requires an argument of type `CreateUserVariables`:
const createUserVars: CreateUserVariables = {
  displayName: ..., 
  email: ..., // optional
  photoUrl: ..., // optional
};

// Call the `createUser()` function to execute the mutation.
// You can use the `await` keyword to wait for the promise to resolve.
const { data } = await createUser(createUserVars);
// Variables can be defined inline as well.
const { data } = await createUser({ displayName: ..., email: ..., photoUrl: ..., });

// You can also pass in a `DataConnect` instance to the action shortcut function.
const dataConnect = getDataConnect(connectorConfig);
const { data } = await createUser(dataConnect, createUserVars);

console.log(data.user_insert);

// Or, you can use the `Promise` API.
createUser(createUserVars).then((response) => {
  const data = response.data;
  console.log(data.user_insert);
});
```

### Using `CreateUser`'s `MutationRef` function

```typescript
import { getDataConnect, executeMutation } from 'firebase/data-connect';
import { connectorConfig, createUserRef, CreateUserVariables } from '@dataconnect/generated';

// The `CreateUser` mutation requires an argument of type `CreateUserVariables`:
const createUserVars: CreateUserVariables = {
  displayName: ..., 
  email: ..., // optional
  photoUrl: ..., // optional
};

// Call the `createUserRef()` function to get a reference to the mutation.
const ref = createUserRef(createUserVars);
// Variables can be defined inline as well.
const ref = createUserRef({ displayName: ..., email: ..., photoUrl: ..., });

// You can also pass in a `DataConnect` instance to the `MutationRef` function.
const dataConnect = getDataConnect(connectorConfig);
const ref = createUserRef(dataConnect, createUserVars);

// Call `executeMutation()` on the reference to execute the mutation.
// You can use the `await` keyword to wait for the promise to resolve.
const { data } = await executeMutation(ref);

console.log(data.user_insert);

// Or, you can use the `Promise` API.
executeMutation(ref).then((response) => {
  const data = response.data;
  console.log(data.user_insert);
});
```

## CreateNoteImage
You can execute the `CreateNoteImage` mutation using the following action shortcut function, or by calling `executeMutation()` after calling the following `MutationRef` function, both of which are defined in [dataconnect-generated/index.d.ts](./index.d.ts):
```typescript
createNoteImage(vars: CreateNoteImageVariables): MutationPromise<CreateNoteImageData, CreateNoteImageVariables>;

interface CreateNoteImageRef {
  ...
  /* Allow users to create refs without passing in DataConnect */
  (vars: CreateNoteImageVariables): MutationRef<CreateNoteImageData, CreateNoteImageVariables>;
}
export const createNoteImageRef: CreateNoteImageRef;
```
You can also pass in a `DataConnect` instance to the action shortcut function or `MutationRef` function.
```typescript
createNoteImage(dc: DataConnect, vars: CreateNoteImageVariables): MutationPromise<CreateNoteImageData, CreateNoteImageVariables>;

interface CreateNoteImageRef {
  ...
  (dc: DataConnect, vars: CreateNoteImageVariables): MutationRef<CreateNoteImageData, CreateNoteImageVariables>;
}
export const createNoteImageRef: CreateNoteImageRef;
```

If you need the name of the operation without creating a ref, you can retrieve the operation name by calling the `operationName` property on the createNoteImageRef:
```typescript
const name = createNoteImageRef.operationName;
console.log(name);
```

### Variables
The `CreateNoteImage` mutation requires an argument of type `CreateNoteImageVariables`, which is defined in [dataconnect-generated/index.d.ts](./index.d.ts). It has the following fields:

```typescript
export interface CreateNoteImageVariables {
  noteProjectId: UUIDString;
  imageUrl: string;
  originalFilename?: string | null;
  status: string;
}
```
### Return Type
Recall that executing the `CreateNoteImage` mutation returns a `MutationPromise` that resolves to an object with a `data` property.

The `data` property is an object of type `CreateNoteImageData`, which is defined in [dataconnect-generated/index.d.ts](./index.d.ts). It has the following fields:
```typescript
export interface CreateNoteImageData {
  noteImage_insert: NoteImage_Key;
}
```
### Using `CreateNoteImage`'s action shortcut function

```typescript
import { getDataConnect } from 'firebase/data-connect';
import { connectorConfig, createNoteImage, CreateNoteImageVariables } from '@dataconnect/generated';

// The `CreateNoteImage` mutation requires an argument of type `CreateNoteImageVariables`:
const createNoteImageVars: CreateNoteImageVariables = {
  noteProjectId: ..., 
  imageUrl: ..., 
  originalFilename: ..., // optional
  status: ..., 
};

// Call the `createNoteImage()` function to execute the mutation.
// You can use the `await` keyword to wait for the promise to resolve.
const { data } = await createNoteImage(createNoteImageVars);
// Variables can be defined inline as well.
const { data } = await createNoteImage({ noteProjectId: ..., imageUrl: ..., originalFilename: ..., status: ..., });

// You can also pass in a `DataConnect` instance to the action shortcut function.
const dataConnect = getDataConnect(connectorConfig);
const { data } = await createNoteImage(dataConnect, createNoteImageVars);

console.log(data.noteImage_insert);

// Or, you can use the `Promise` API.
createNoteImage(createNoteImageVars).then((response) => {
  const data = response.data;
  console.log(data.noteImage_insert);
});
```

### Using `CreateNoteImage`'s `MutationRef` function

```typescript
import { getDataConnect, executeMutation } from 'firebase/data-connect';
import { connectorConfig, createNoteImageRef, CreateNoteImageVariables } from '@dataconnect/generated';

// The `CreateNoteImage` mutation requires an argument of type `CreateNoteImageVariables`:
const createNoteImageVars: CreateNoteImageVariables = {
  noteProjectId: ..., 
  imageUrl: ..., 
  originalFilename: ..., // optional
  status: ..., 
};

// Call the `createNoteImageRef()` function to get a reference to the mutation.
const ref = createNoteImageRef(createNoteImageVars);
// Variables can be defined inline as well.
const ref = createNoteImageRef({ noteProjectId: ..., imageUrl: ..., originalFilename: ..., status: ..., });

// You can also pass in a `DataConnect` instance to the `MutationRef` function.
const dataConnect = getDataConnect(connectorConfig);
const ref = createNoteImageRef(dataConnect, createNoteImageVars);

// Call `executeMutation()` on the reference to execute the mutation.
// You can use the `await` keyword to wait for the promise to resolve.
const { data } = await executeMutation(ref);

console.log(data.noteImage_insert);

// Or, you can use the `Promise` API.
executeMutation(ref).then((response) => {
  const data = response.data;
  console.log(data.noteImage_insert);
});
```

## CreateTranscription
You can execute the `CreateTranscription` mutation using the following action shortcut function, or by calling `executeMutation()` after calling the following `MutationRef` function, both of which are defined in [dataconnect-generated/index.d.ts](./index.d.ts):
```typescript
createTranscription(vars: CreateTranscriptionVariables): MutationPromise<CreateTranscriptionData, CreateTranscriptionVariables>;

interface CreateTranscriptionRef {
  ...
  /* Allow users to create refs without passing in DataConnect */
  (vars: CreateTranscriptionVariables): MutationRef<CreateTranscriptionData, CreateTranscriptionVariables>;
}
export const createTranscriptionRef: CreateTranscriptionRef;
```
You can also pass in a `DataConnect` instance to the action shortcut function or `MutationRef` function.
```typescript
createTranscription(dc: DataConnect, vars: CreateTranscriptionVariables): MutationPromise<CreateTranscriptionData, CreateTranscriptionVariables>;

interface CreateTranscriptionRef {
  ...
  (dc: DataConnect, vars: CreateTranscriptionVariables): MutationRef<CreateTranscriptionData, CreateTranscriptionVariables>;
}
export const createTranscriptionRef: CreateTranscriptionRef;
```

If you need the name of the operation without creating a ref, you can retrieve the operation name by calling the `operationName` property on the createTranscriptionRef:
```typescript
const name = createTranscriptionRef.operationName;
console.log(name);
```

### Variables
The `CreateTranscription` mutation requires an argument of type `CreateTranscriptionVariables`, which is defined in [dataconnect-generated/index.d.ts](./index.d.ts). It has the following fields:

```typescript
export interface CreateTranscriptionVariables {
  noteImageId: UUIDString;
  transcribedText: string;
}
```
### Return Type
Recall that executing the `CreateTranscription` mutation returns a `MutationPromise` that resolves to an object with a `data` property.

The `data` property is an object of type `CreateTranscriptionData`, which is defined in [dataconnect-generated/index.d.ts](./index.d.ts). It has the following fields:
```typescript
export interface CreateTranscriptionData {
  transcription_insert: Transcription_Key;
}
```
### Using `CreateTranscription`'s action shortcut function

```typescript
import { getDataConnect } from 'firebase/data-connect';
import { connectorConfig, createTranscription, CreateTranscriptionVariables } from '@dataconnect/generated';

// The `CreateTranscription` mutation requires an argument of type `CreateTranscriptionVariables`:
const createTranscriptionVars: CreateTranscriptionVariables = {
  noteImageId: ..., 
  transcribedText: ..., 
};

// Call the `createTranscription()` function to execute the mutation.
// You can use the `await` keyword to wait for the promise to resolve.
const { data } = await createTranscription(createTranscriptionVars);
// Variables can be defined inline as well.
const { data } = await createTranscription({ noteImageId: ..., transcribedText: ..., });

// You can also pass in a `DataConnect` instance to the action shortcut function.
const dataConnect = getDataConnect(connectorConfig);
const { data } = await createTranscription(dataConnect, createTranscriptionVars);

console.log(data.transcription_insert);

// Or, you can use the `Promise` API.
createTranscription(createTranscriptionVars).then((response) => {
  const data = response.data;
  console.log(data.transcription_insert);
});
```

### Using `CreateTranscription`'s `MutationRef` function

```typescript
import { getDataConnect, executeMutation } from 'firebase/data-connect';
import { connectorConfig, createTranscriptionRef, CreateTranscriptionVariables } from '@dataconnect/generated';

// The `CreateTranscription` mutation requires an argument of type `CreateTranscriptionVariables`:
const createTranscriptionVars: CreateTranscriptionVariables = {
  noteImageId: ..., 
  transcribedText: ..., 
};

// Call the `createTranscriptionRef()` function to get a reference to the mutation.
const ref = createTranscriptionRef(createTranscriptionVars);
// Variables can be defined inline as well.
const ref = createTranscriptionRef({ noteImageId: ..., transcribedText: ..., });

// You can also pass in a `DataConnect` instance to the `MutationRef` function.
const dataConnect = getDataConnect(connectorConfig);
const ref = createTranscriptionRef(dataConnect, createTranscriptionVars);

// Call `executeMutation()` on the reference to execute the mutation.
// You can use the `await` keyword to wait for the promise to resolve.
const { data } = await executeMutation(ref);

console.log(data.transcription_insert);

// Or, you can use the `Promise` API.
executeMutation(ref).then((response) => {
  const data = response.data;
  console.log(data.transcription_insert);
});
```

