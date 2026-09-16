import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { SchemaCatalogEntry, DBMS, TableSchema, DocumentTemplate, DocumentTemplateItem } from '@/types'
import type { ChangeSpec, ReviewResult, SqlPack, ChangeDocument } from '@/api/client'

const SPEC_STORAGE_PREFIX = 'cs:'
const SCHEMA_STORAGE_KEY = 'cs:schemaCatalog'
const TEMPLATE_STORAGE_KEY = 'cs:templateCatalog'

function loadSchemaCatalog(): SchemaCatalogEntry[] {
  try {
    const raw = localStorage.getItem(SCHEMA_STORAGE_KEY)
    if (!raw) return defaultSchemaCatalog()
    const parsed = JSON.parse(raw)
    if (!Array.isArray(parsed)) return defaultSchemaCatalog()
    return parsed.map((entry: unknown) => castSchemaEntry(entry))
  } catch {
    return defaultSchemaCatalog()
  }
}

function defaultSchemaCatalog(): SchemaCatalogEntry[] {
  return [
    {
      id: 'default',
      name: '기본 스키마',
      dbms: 'POSTGRESQL' as DBMS,
      database: 'app',
      schema: 'public',
      tables: [
        {
          name: 'orders',
          columns: [
            { name: 'id', data_type: 'bigint', nullable: false },
            { name: 'tenant_id', data_type: 'bigint', nullable: false },
            { name: 'status', data_type: 'varchar', nullable: false },
            { name: 'created_at', data_type: 'timestamp', nullable: false },
          ],
          primary_key_columns: ['id'],
        },
      ],
      updatedAt: new Date().toISOString(),
      tableCount: 1,
      columnCount: 4,
      used: true,
    },
  ]
}

function castSchemaEntry(entry: unknown): SchemaCatalogEntry {
  const e = entry as Record<string, unknown>
  const tables = (e.tables ?? []) as TableSchema[]
  const tableCount = Array.isArray(tables) ? tables.length : 0
  const columnCount = Array.isArray(tables)
    ? tables.reduce((sum, t) => sum + (Array.isArray(t.columns) ? t.columns.length : 0), 0)
    : 0
  return {
    id: String(e.id ?? ''),
    name: String(e.name ?? ''),
    dbms: (e.dbms ?? 'POSTGRESQL') as DBMS,
    database: String(e.database ?? ''),
    schema: String(e.schema ?? ''),
    tables,
    updatedAt: String(e.updatedAt ?? ''),
    tableCount,
    columnCount,
    used: Boolean(e.used),
  }
}

function saveSchemaCatalog(list: SchemaCatalogEntry[]): void {
  try {
    localStorage.setItem(SCHEMA_STORAGE_KEY, JSON.stringify(list))
  } catch {
    // storage full or unavailable
  }
}

function loadTemplateCatalog(): DocumentTemplate[] {
  try {
    const raw = localStorage.getItem(TEMPLATE_STORAGE_KEY)
    if (!raw) return defaultTemplateCatalog()
    const parsed = JSON.parse(raw)
    if (!Array.isArray(parsed)) return defaultTemplateCatalog()
    return parsed.map((item: unknown) => castTemplate(item))
  } catch {
    return defaultTemplateCatalog()
  }
}

function defaultTemplateCatalog(): DocumentTemplate[] {
  const defaultItems = defaultTemplateItems()
  const securityItems = securityTemplateItems()
  const simpleItems = simpleTemplateItems()
  return [
    {
      id: 'default',
      name: '기본 변경 신청서',
      isDefault: true,
      itemCount: defaultItems.length,
      items: defaultItems,
    },
    {
      id: 'security',
      name: '보안팀 신청서',
      isDefault: false,
      itemCount: securityItems.length,
      items: securityItems,
    },
    {
      id: 'simple',
      name: '간이 신청서',
      isDefault: false,
      itemCount: simpleItems.length,
      items: simpleItems,
    },
  ]
}

function defaultTemplateItems(): DocumentTemplateItem[] {
  return [
    { name: '변경 요청 원문', source: 'requestOrigin' },
    { name: '대상 테이블', source: 'targetTable' },
    { name: '변경 작업', source: 'operation' },
    { name: '대상 조건', source: 'predicates' },
    { name: '변경 값', source: 'mutations' },
    { name: '식별 키', source: 'identityKeyColumns' },
    { name: '예상 영향 건수', source: 'expectedRowCount' },
    { name: '확인 SQL', source: 'precheckSql' },
    { name: '백업 SQL', source: 'backupSql' },
    { name: '실행 SQL', source: 'executionSql' },
    { name: '검증 SQL', source: 'verificationSql' },
    { name: '롤백 SQL', source: 'rollbackSql' },
  ]
}

function securityTemplateItems(): DocumentTemplateItem[] {
  return [
    { name: '변경 요청 원문', source: 'requestOrigin' },
    { name: '대상 테이블', source: 'targetTable' },
    { name: '변경 작업', source: 'operation' },
    { name: '대상 조건', source: 'predicates' },
    { name: '변경 값', source: 'mutations' },
    { name: '승인자', source: 'approver' },
  ]
}

function simpleTemplateItems(): DocumentTemplateItem[] {
  return [
    { name: '대상 테이블', source: 'targetTable' },
    { name: '변경 작업', source: 'operation' },
    { name: '실행 SQL', source: 'executionSql' },
  ]
}

function castTemplate(item: unknown): DocumentTemplate {
  const t = item as Record<string, unknown>
  const items = ((t.items ?? []) as unknown[]).map((it: unknown) => ({
    name: String((it as Record<string, unknown>).name ?? ''),
    source: String((it as Record<string, unknown>).source ?? 'requestOrigin'),
    value: typeof (it as Record<string, unknown>).value === 'string' ? ((it as Record<string, unknown>).value as string) : undefined,
  }))
  return {
    id: String(t.id ?? ''),
    name: String(t.name ?? ''),
    isDefault: Boolean(t.isDefault),
    itemCount: items.length,
    items,
  }
}

function saveTemplateCatalog(list: DocumentTemplate[]): void {
  try {
    localStorage.setItem(TEMPLATE_STORAGE_KEY, JSON.stringify(list))
  } catch {
    // storage full or unavailable
  }
}

export const useAppStore = defineStore('app', () => {
  const currentSpecId = ref<string | null>(null)
  const currentSpecStatus = ref<string | null>(null)

  const spec = ref<ChangeSpec | null>(null)
  const sqlPack = ref<SqlPack | null>(null)
  const baselineSqlPack = ref<SqlPack | null>(null)
  const confirmedArtifacts = ref<Set<string>>(new Set())
  const evidence = ref({
    executionPlanReviewed: false,
    indexReviewed: false,
    lockReviewed: false,
    concurrencyReviewed: false,
  })
  const review = ref<ReviewResult | null>(null)
  const document = ref<ChangeDocument | null>(null)
  const editableDocumentValues = ref<Record<string, string>>({})
  const notFound = ref(false)

  const schemaList = ref<SchemaCatalogEntry[]>(loadSchemaCatalog())
  const documentTemplates = ref<DocumentTemplate[]>(loadTemplateCatalog())

  const supportedDbmses = [
    'POSTGRESQL',
    'MYSQL',
    'MARIADB',
    'ORACLE',
    'SQL_SERVER',
    'SQLITE',
    'BIGQUERY',
    'SNOWFLAKE',
  ] as DBMS[]

  const activeSchemaId = ref<string | null>(schemaList.value[0]?.id ?? null)

  const activeSchema = computed(() => {
    if (!activeSchemaId.value) return schemaList.value[0] ?? null
    return schemaList.value.find((s) => s.id === activeSchemaId.value) ?? schemaList.value[0] ?? null
  })

  const recentSpecs = ref<Array<{ specId: string; status: string; originalRequest: string; lastStep: number }>>([])

  function persistSchemaCatalog() {
    saveSchemaCatalog(schemaList.value)
  }

  function persistTemplateCatalog() {
    saveTemplateCatalog(documentTemplates.value)
  }

  function setSpec(specId: string, status: string) {
    currentSpecId.value = specId
    currentSpecStatus.value = status
    notFound.value = false
    pushRecent(specId, status)
  }

  function pushRecent(specId: string, status: string) {
    const existing = recentSpecs.value.findIndex((r) => r.specId === specId)
    const entry = {
      specId,
      status,
      originalRequest: spec.value?.originalRequest ?? '',
      lastStep: status === 'CONFIRMED' ? 3 : status === 'DRAFT' ? 1 : 1,
    }
    if (existing >= 0) {
      recentSpecs.value.splice(existing, 1)
    }
    recentSpecs.value.unshift(entry)
    if (recentSpecs.value.length > 3) {
      recentSpecs.value.length = 3
    }
  }

  function setNotFound() {
    currentSpecId.value = null
    currentSpecStatus.value = null
    notFound.value = true
  }

  function setSpecData(data: ChangeSpec) {
    spec.value = data
    setSpec(data.specId, data.status)
    persistCurrentFlowState()
  }

  function setSqlPackData(pack: SqlPack) {
    sqlPack.value = pack
    if (!baselineSqlPack.value) {
      baselineSqlPack.value = pack
    }
    persistCurrentFlowState()
  }

  function setBaselineSqlPack(pack: SqlPack) {
    baselineSqlPack.value = pack
    persistCurrentFlowState()
  }

  function markArtifactConfirmed(name: string) {
    confirmedArtifacts.value.add(name)
    persistCurrentFlowState()
  }

  function clearConfirmedArtifacts() {
    confirmedArtifacts.value.clear()
    persistCurrentFlowState()
  }

  function setReviewData(data: ReviewResult) {
    review.value = data
    persistCurrentFlowState()
  }

  function setDocumentData(data: ChangeDocument) {
    document.value = data
    persistCurrentFlowState()
  }

  function persistCurrentFlowState() {
    if (!currentSpecId.value) {
      localStorage.removeItem(`${SPEC_STORAGE_PREFIX}${currentSpecId.value}`)
      return
    }
    const state = {
      specId: currentSpecId.value,
      status: currentSpecStatus.value,
      sqlPack: sqlPack.value ? serializeSqlPack(sqlPack.value) : null,
      baselineSqlPack: baselineSqlPack.value ? serializeSqlPack(baselineSqlPack.value) : null,
      confirmedArtifacts: Array.from(confirmedArtifacts.value),
      evidence: evidence.value,
      review: review.value ? serializeReview(review.value) : null,
      document: document.value ? serializeDocument(document.value) : null,
    }
    try {
      localStorage.setItem(`${SPEC_STORAGE_PREFIX}${currentSpecId.value}`, JSON.stringify(state))
    } catch {
      // ignore
    }
  }

  function loadFlowState(specId: string) {
    try {
      const raw = localStorage.getItem(`${SPEC_STORAGE_PREFIX}${specId}`)
      if (!raw) return
      const state = JSON.parse(raw) as {
        specId?: string
        status?: string
        sqlPack?: ReturnType<typeof serializeSqlPack>
        baselineSqlPack?: ReturnType<typeof serializeSqlPack>
        confirmedArtifacts?: string[]
        evidence?: ReturnType<typeof serializeEvidence>
        review?: ReturnType<typeof serializeReview>
        document?: ReturnType<typeof serializeDocument>
      }
      if (state.specId) currentSpecId.value = state.specId
      if (state.status) currentSpecStatus.value = state.status
      if (state.sqlPack) sqlPack.value = deserializeSqlPack(state.sqlPack)
      if (state.baselineSqlPack) baselineSqlPack.value = deserializeSqlPack(state.baselineSqlPack)
      if (state.confirmedArtifacts) confirmedArtifacts.value = new Set(state.confirmedArtifacts)
      if (state.evidence) evidence.value = state.evidence as typeof evidence.value
      if (state.review) review.value = deserializeReview(state.review)
      if (state.document) document.value = deserializeDocument(state.document)
    } catch {
      // ignore
    }
  }

  function clearFlowState() {
    if (currentSpecId.value) {
      localStorage.removeItem(`${SPEC_STORAGE_PREFIX}${currentSpecId.value}`)
    }
  }

  function serializeSqlPack(pack: SqlPack): object {
    return {
      precheckSql: pack.precheckSql,
      backupSql: pack.backupSql,
      executionSql: pack.executionSql,
      verificationSql: pack.verificationSql,
      rollbackSql: pack.rollbackSql,
      rollbackStatus: pack.rollbackStatus,
      specId: pack.specId,
      specVersion: pack.specVersion,
      contentHash: pack.contentHash,
      revision: pack.revision,
      updatedAt: pack.updatedAt,
    }
  }

  function deserializeSqlPack(data: object): SqlPack {
    const d = data as Record<string, unknown>
    return {
      precheckSql: String(d.precheckSql ?? ''),
      backupSql: String(d.backupSql ?? ''),
      executionSql: String(d.executionSql ?? ''),
      verificationSql: String(d.verificationSql ?? ''),
      rollbackSql: String(d.rollbackSql ?? ''),
      rollbackStatus: String(d.rollbackStatus ?? 'TEMPLATE_REQUIRES_BACKUP_ROWS'),
      specId: String(d.specId ?? ''),
      specVersion: Number(d.specVersion ?? 1),
      contentHash: String(d.contentHash ?? ''),
      revision: Number(d.revision ?? 1),
      updatedAt: String(d.updatedAt ?? new Date().toISOString()),
    }
  }

  function serializeReview(review: ReviewResult): object {
    return {
      specId: review.specId,
      specVersion: review.specVersion,
      contentHash: review.contentHash,
      sqlPackRevision: review.sqlPackRevision,
      verdict: review.verdict,
      riskLevel: review.riskLevel,
      isStale: review.isStale,
      checks: review.checks.map((c) => ({
        ruleId: c.ruleId,
        category: c.category,
        status: c.status,
        severity: c.severity,
        message: c.message,
        expected: c.expected,
        actual: c.actual,
        specField: c.specField,
        sqlArtifact: c.sqlArtifact,
        sqlLocation: c.sqlLocation,
        suggestedFix: c.suggestedFix,
      })),
      disclaimer: review.disclaimer,
      reviewedAt: review.reviewedAt,
    }
  }

  function deserializeReview(data: object): ReviewResult {
    const d = data as Record<string, unknown>
    return {
      specId: String(d.specId ?? ''),
      specVersion: Number(d.specVersion ?? 1),
      contentHash: String(d.contentHash ?? ''),
      sqlPackRevision: Number(d.sqlPackRevision ?? 1),
      verdict: String(d.verdict ?? 'READY'),
      riskLevel: String(d.riskLevel ?? 'LOW'),
      isStale: Boolean(d.isStale ?? false),
      checks: ((d.checks ?? []) as unknown[]).map((c: unknown) => {
        const o = c as Record<string, unknown>
        return {
          ruleId: String(o.ruleId ?? ''),
          category: String(o.category ?? ''),
          status: String(o.status ?? 'PASS'),
          severity: String(o.severity ?? 'INFO'),
          message: String(o.message ?? ''),
          expected: o.expected,
          actual: o.actual,
          specField: typeof o.specField === 'string' ? o.specField : null,
          sqlArtifact: typeof o.sqlArtifact === 'string' ? o.sqlArtifact : null,
          sqlLocation: typeof o.sqlLocation === 'string' ? o.sqlLocation : null,
          suggestedFix: typeof o.suggestedFix === 'string' ? o.suggestedFix : null,
        }
      }),
      disclaimer: String(d.disclaimer ?? ''),
      reviewedAt: String(d.reviewedAt ?? new Date().toISOString()),
    }
  }

  function serializeDocument(doc: ChangeDocument): object {
    return {
      specId: doc.specId,
      specVersion: doc.specVersion,
      contentHash: doc.contentHash,
      sqlPackRevision: doc.sqlPackRevision,
      templateName: doc.templateName,
      fields: doc.fields.map((f) => ({
        key: f.key,
        label: f.label,
        value: f.value,
        required: f.required,
        source: f.source,
      })),
      generatedAt: doc.generatedAt,
    }
  }

  function deserializeDocument(data: object): ChangeDocument {
    const d = data as Record<string, unknown>
    return {
      specId: String(d.specId ?? ''),
      specVersion: Number(d.specVersion ?? 1),
      contentHash: String(d.contentHash ?? ''),
      sqlPackRevision: Number(d.sqlPackRevision ?? 1),
      templateName: String(d.templateName ?? 'DEFAULT'),
      fields: ((d.fields ?? []) as unknown[]).map((f: unknown) => {
        const o = f as Record<string, unknown>
        return {
          key: String(o.key ?? ''),
          label: String(o.label ?? ''),
          value: o.value,
          required: Boolean(o.required ?? false),
          source: String(o.source ?? 'CHANGE_SPEC'),
        }
      }),
      generatedAt: String(d.generatedAt ?? new Date().toISOString()),
    }
  }

  function serializeEvidence(ev: typeof evidence.value): Record<string, boolean> {
    return { ...ev }
  }

  return {
    currentSpecId,
    currentSpecStatus,
    spec,
    sqlPack,
    baselineSqlPack,
    confirmedArtifacts,
    evidence,
    review,
    document,
    editableDocumentValues,
    notFound,
    schemaList,
    documentTemplates,
    supportedDbmses,
    activeSchemaId,
    activeSchema,
    recentSpecs,
    setSpec,
    setNotFound,
    setSpecData,
    setSqlPackData,
    setBaselineSqlPack,
    markArtifactConfirmed,
    clearConfirmedArtifacts,
    setReviewData,
    setDocumentData,
    persistSchemaCatalog,
    persistTemplateCatalog,
    loadFlowState,
    clearFlowState,
  }
})

