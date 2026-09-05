class MemoryErrorBase(Exception):
    """Base class for stable semantic runtime failures."""


class MemoryWriteConflict(MemoryErrorBase): pass
class MemoryUnknownWriteOutcome(MemoryErrorBase): pass
class MemoryOriginOpaque(MemoryErrorBase): pass
class MemoryAdmissionRejected(MemoryErrorBase): pass
class MemoryTransitionIncomplete(MemoryErrorBase): pass
class MemoryScopeBlocked(MemoryErrorBase): pass
class MemoryQueryIncomplete(MemoryErrorBase): pass
class MemoryQueryCapabilityUnsupported(MemoryErrorBase): pass
class MemoryRecallAmbiguous(MemoryErrorBase): pass
class MemoryRecallInsufficient(MemoryErrorBase): pass
class MemoryViewOverflow(MemoryErrorBase): pass
class MemoryRecoverabilityLost(MemoryErrorBase): pass
class MemoryIntegrityError(MemoryErrorBase): pass
class MemoryStaleWriter(MemoryErrorBase): pass
class MemoryIndexFrontierIncomplete(MemoryErrorBase): pass
class MemoryIrrecoverableGap(MemoryErrorBase): pass
class IdempotencyConflict(MemoryErrorBase): pass
class MemoryIdentityCollision(MemoryErrorBase): pass
class MemoryDependencyStale(MemoryErrorBase): pass
class ActionArgumentMismatch(MemoryErrorBase): pass
class MemoryFenceReplay(MemoryErrorBase): pass
class MemoryFenceExpired(MemoryErrorBase): pass
class MemoryClockAuthorityRequired(MemoryErrorBase): pass
class MemoryFenceBindingMismatch(MemoryErrorBase): pass
class MemoryCutUnavailable(MemoryErrorBase): pass
class MemoryDebtTransitionInvalid(MemoryErrorBase): pass
class MemoryRetentionBlocked(MemoryErrorBase): pass
class MemoryFlowBlocked(MemoryErrorBase): pass
class MemoryFlowOpaque(MemoryErrorBase): pass
class MemoryRecoveryBlocked(MemoryErrorBase): pass
class MemoryErasureIncomplete(MemoryErrorBase): pass
class MemoryContinuityInvalid(MemoryErrorBase): pass
class MemoryPublicationBlocked(MemoryErrorBase): pass
class MemoryAmbiguousSuccessors(MemoryErrorBase): pass
class MemoryDegradedCapability(MemoryErrorBase): pass
class MemoryCounterexampleUnresolved(MemoryErrorBase): pass
class MemoryAccessCapabilityDenied(MemoryErrorBase): pass
class MemoryFlowPolicyCurrentnessUnknown(MemoryDependencyStale): pass
class MemoryUseValidationUnavailable(MemoryErrorBase): pass

class MemoryProposalStale(MemoryErrorBase): pass
