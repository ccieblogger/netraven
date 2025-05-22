<template>
  <div class="max-w-4xl mx-auto py-8">
    <div v-if="loading" class="text-center py-8 text-gray-500">Loading job metadata...</div>
    <div v-else-if="error" class="text-center py-8 text-red-600">{{ error }}</div>
    <div v-else>
      <JobForm
        :metadata="metadata"
        @run-now="onRunNow"
        @schedule-job="onScheduleJob"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import JobForm from '../components/JobForm.vue';
import axios from 'axios';

const route = useRoute();
const router = useRouter();
const jobType = route.params.name;
const metadata = ref(null);
const loading = ref(true);
const error = ref(null);

async function fetchMetadata() {
  loading.value = true;
  error.value = null;
  try {
    const res = await axios.get(`/jobs/metadata/${jobType}`);
    metadata.value = res.data;
  } catch (e) {
    error.value = e?.response?.data?.detail || 'Failed to load job metadata.';
  } finally {
    loading.value = false;
  }
}

function onRunNow({ rawParams, schedule }) {
  axios.post('/jobs/execute', {
    name: jobType,
    raw_parameters: rawParams,
    schedule
  })
    .then(() => {
      router.push('/jobs');
    })
    .catch(e => {
      alert(e?.response?.data?.detail || 'Failed to run job.');
    });
}

function onScheduleJob({ rawParams, schedule }) {
  axios.post('/jobs/execute', {
    name: jobType,
    raw_parameters: rawParams,
    schedule
  })
    .then(() => {
      router.push('/jobs');
    })
    .catch(e => {
      alert(e?.response?.data?.detail || 'Failed to schedule job.');
    });
}

onMounted(fetchMetadata);
</script>

<style scoped>
</style>
