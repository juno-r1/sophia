# Sophia Integrations

## SI-0

Sophia Integrations, abbreviated as SIs, are internal tickets used to implement the specification of the Sophia interpreter. SIs are numbered in order of creation: this one is SI-0. The ordering is permanent.

SIs are associated with a description of their requirements, an integration test, and the unit tests used for the components associated with the SI. Unit tests may be changed and reordered as is necessary.

## SI-1

Initialise the Sophia runtime.

## SI-2

Return statement.

`return`
`return <E>`

Ends execution of the current routine and returns null to the calling routine.
It is possible to return from the global routine.
The returned value may be used by external utilities in future.