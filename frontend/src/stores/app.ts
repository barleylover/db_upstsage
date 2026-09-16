import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { SchemaCatalogEntry, DBMS } from '@/types'
import type { ChangeSpec, ReviewResult, SqlPack, ChangeDocument } from '@/api/client'

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
  const notFound = ref(false)

  const schemaList = ref<SchemaCatalogEntry[]>([
    {
      id: 'default',
      name: '기본 스키마',
      dbms: 'POSTGRESQL',
      database: 'app',
      schema: 'public',
      tableCount: 1,
      columnCount: 4,
      used: true,
    },
    {
      id: 'pay',
      name: '결제 DB',
      dbms: 'MYSQL',
      database: 'pay',
      schema: 'public',
      tableCount: 1,
      columnCount: 3,
      used: false,
    },
  ])

  const documentTemplates = ref([
    { id: 'default', name: '기본 변경 신청서', itemCount: 12, isDefault: true, items: [] },
    { id: 'security', name: '보안팀 신청서', itemCount: 6, isDefault: false, items: [] },
    { id: 'simple', name: '간이 신청서', itemCount: 3, isDefault: false, items: [] },
  ])

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

  const activeSchemaId = ref<string | null>('default')
  const activeSchema = ref<SchemaCatalogEntry | null>(null)

  function setSpec(specId: string, status: string) {
    currentSpecId.value = specId
    currentSpecStatus.value = status
    notFound.value = false
  }

  function setNotFound() {
    currentSpecId.value = null
    currentSpecStatus.value = null
    notFound.value = true
  }

  function setSpecData(data: ChangeSpec) {
    spec.value = data
    setSpec(data.specId, data.status)
  }

  function setSqlPackData(pack: SqlPack) {
    sqlPack.value = pack
    if (!baselineSqlPack.value) {
      baselineSqlPack.value = pack
    }
  }

  function setBaselineSqlPack(pack: SqlPack) {
    baselineSqlPack.value = pack
  }

  function markArtifactConfirmed(name: string) {
    confirmedArtifacts.value.add(name)
  }

  function clearConfirmedArtifacts() {
    confirmedArtifacts.value.clear()
  }

  function setReviewData(data: ReviewResult) {
    review.value = data
  }

  function setDocumentData(data: ChangeDocument) {
    document.value = data
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
    notFound,
    schemaList,
    documentTemplates,
    supportedDbmses,
    activeSchemaId,
    activeSchema,
    setSpec,
    setNotFound,
    setSpecData,
    setSqlPackData,
    setBaselineSqlPack,
    markArtifactConfirmed,
    clearConfirmedArtifacts,
    setReviewData,
    setDocumentData,
  }
})
