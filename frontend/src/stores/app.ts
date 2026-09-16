import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { SchemaCatalogEntry, DBMS } from '@/types'

export const useAppStore = defineStore('app', () => {
  const currentSpecId = ref<string | null>(null)
  const currentSpecStatus = ref<string | null>(null)
  const demoMode = ref(true)

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
  const activeSchema = computed(() => schemaList.value.find((s) => s.id === activeSchemaId.value) ?? schemaList.value[0])

  function setSpec(specId: string, status: string) {
    currentSpecId.value = specId
    currentSpecStatus.value = status
  }

  return {
    currentSpecId,
    currentSpecStatus,
    demoMode,
    schemaList,
    documentTemplates,
    supportedDbmses,
    activeSchemaId,
    activeSchema,
    setSpec,
  }
})
