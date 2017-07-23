function onload() {

/*------------------------------------------------------------------------------
  lib
------------------------------------------------------------------------------*/

function format_elapsed(elapsed) {
  return (
      elapsed < 1e-5 ? (elapsed * 1e6).toPrecision(2) + " µs"
    : elapsed < 1e-3 ? (elapsed * 1e6).toPrecision(3) + " µs"
    : elapsed < 1e-2 ? (elapsed * 1e3).toPrecision(2) + " ms"
    : elapsed < 1e+0 ? (elapsed * 1e3).toPrecision(3) + " ms"
    : elapsed < 1e+1 ? (elapsed      ).toPrecision(2) + " s"
    : elapsed < 60   ? (elapsed      ).toPrecision(3) + " s"
    : elapsed < 3600 ? 
          Math.trunc(elapsed / 60) 
        + ":" + Math.trunc(elapsed % 60).padStart(2, "0")
    :     Math.trunc(elapsed / 3660) 
        + ":" + Math.trunc(elapsed / 60 % 60).padStart(2, "0")
        + ":" + Math.trunc(elapsed % 60).padStart(2, "0")
  )
}

/*------------------------------------------------------------------------------
  Components
------------------------------------------------------------------------------*/

Vue.component('action-url', {
  props: ['action', 'url'],
  template: `
    <span class="action" v-on:click="do_action(url)">
      {{ action }}
    </span>
  `,

  methods: {
    do_action(url) {
      fetch(url, { method: "POST" })
    },
  },

})

/*------------------------------------------------------------------------------
  jobs
------------------------------------------------------------------------------*/

const jobs_template = `
<div>
  <br>
  <table class="joblist">
    <thead>
      <tr>
        <th>Job ID</th>
        <th>Program</th>
        <th>Schedule</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="job in jobs" v-on:click="$router.push({ name: 'job', params: { job_id: job.job_id } })">
        <td class="job-link">{{ job.job_id }}</td>
        <td>{{ job.program.str || "" }}</td>
        <td>
          <template v-for="s in job.schedules">
            {{ s.str }}
            <br>
          </template>
        </td>
      </tr>
    </tbody>
  </table>
</div>
`

const Jobs = { 
  template: jobs_template,
  data() {
    return {
      jobs: [],
    }
  },

  created() {
    const v = this
    const url = "/api/v1/jobs"
    fetch(url)
      .then((response) => response.json())
      .then((response) => response.forEach((j) => v.jobs.push(j)))
  },
}

/*------------------------------------------------------------------------------
  job
------------------------------------------------------------------------------*/

/* FIXME: Not used; remove these, and accompanying CSS.  */

Vue.component('js-el', {
  props: ['val'],
  template: `
    <div class="js-el" style="clear: both;">
      <array-ol v-if="Array.isArray(val)" v-bind:arr="val"></array-ol>
      <object-dl v-else-if="!Array.isArray(val) && typeof val == 'object'" v-bind:obj="val"></object-dl>
      <template v-else>{{ val }}</template>
    </div>
  `,
})

Vue.component('object-dl', {
  props: ['obj'],
  template: `
    <dl>
      <template v-if="obj['$type'] !== undefined">
        <dt>{{ obj['$type'] }}</dt>
        <dd>&nbsp;</dd>
      </template>
      <template v-for="(val, key) in obj" v-if="key != '$type'">
        <dt>{{ key }}</dt>
        <dd><js-el v-bind:val="val"></js-el></dd>
      </template>
    </dl>
  `,
})

Vue.component('array-ol', {
  props: ['arr'],
  template: `
    <ol start="0">
      <li v-for="val in arr">
        <js-el v-bind:val="val"></js-el>
      </li>
    </ol>
  `,
})


const job_template = `
<div>
  <br>
  <h4>{{ job_id }}</h4>

  <dl v-if="job">
    <dt>Parameters</dt>
    <dd>{{ _.join(", ")(job.params) }}</dd>

    <dt>Program</dt>
    <dd>{{ job.program.str }}</dd>

    <template v-for="schedule in job.schedules">
      <dt>Schedule</dt>
      <dd>{{ schedule.str }}</dd>
    </template>
  </dl>

  <runs v-bind:job_id="job_id"></runs>
</div>
`

const Job = {
  template: job_template,
  props: ['job_id'],
  data() {
    return {
      job: null,
    }
  },

  created() {
    const v = this
    const url = "/api/v1/jobs/" + this.job_id  // FIXME
    fetch(url)
      .then((response) => response.json())
      .then((response) => { v.job = response })
  },
}

/*------------------------------------------------------------------------------
  instances
------------------------------------------------------------------------------*/

const insts_template = `
<div>
  <br>
  <table class="inst-list">
    <thead>
      <tr>
        <th>Job</th>
        <th>Args</th>
        <th>Runs</th>
        <th>State</th>
        <th>Actions</th>
      </tr>
    </thead>
    <tbody>
      <template v-for="inst in insts">

        <!-- A row for the inst.  -->
        <tr>
          <td class="job-link" 
              v-on:click="$router.push({ name: 'job', params: { job_id: inst.job_id } })"
          >{{ inst.job_id }}</td>
          <td>{{ inst.args }}</td>
          <td>
            {{ inst.runs.length }}
            <span 
                v-if="expanded[inst.inst_id]" 
                v-on:click="expand(inst.inst_id, false)">
              V
            </span>
            <span 
                v-else
                v-on:click="expand(inst.inst_id, true)">
              &gt;
            </span>
          </td>
          <template v-if="! expanded[inst.inst_id]">
            <td>{{ inst.run.state }}</td>
            <td>
              <action-url 
                  v-for="(url, action) in inst.run.actions"
                  :action="action" :url="url">
              </action-url>
            </td>
          </template>
        </tr>

        <!-- A row for each run.  -->
        <tr v-if="expanded[inst.inst_id]" 
            v-for="run in inst.runs"
            class="run">
          <td colspan="2"></td>
          <td class="run-link" 
              v-on:click="$router.push({ name: 'run', params: { run_id: run.run_id } })">
            {{ run.run_id }}
          </td>
          <td>{{ run.state }}</td>
          <td>
            <action-url 
                v-for="(url, action) in run.actions"
                :action="action" :url="url">
            </action-url>
          </td>
        </tr>

      </template>
    </tbody>
  </table>
</div>
`

const Insts = {
  template: insts_template,
  props: [],
  data() {
    return {
      runs: null,
      expanded: {},
    }
  },

  computed: {
    insts() {
      if (this.runs === null)
        return null
      const insts = {}
      // Group runs by inst.
      for (run_id in this.runs) {
        const run = this.runs[run_id]
        var inst = insts[run.inst_id]
        if (inst === undefined)
          inst = insts[run.inst_id] = {
            inst_id : run.inst_id,
            job_id  : run.job_id,
            args    : _.flow([
                _.toPairs,
                _.map(([k, v]) => k + "=" + v),
                _.join(" ")
              ])(run.args),
            runs    : [run],
          }
        // Arrange runs by run number.  Assume these are dense.
        inst.runs[run.number] = run
      }
      for (inst_id in insts) {
        const inst = insts[inst_id]
        // Sort runs by run number.
        inst.runs = _.sortBy(r => r.number)(inst.runs)
        // Show runs-specific information for the last run.
        inst.run = _.last(inst.runs)
      }
      // Sort by time.
      return _.sortBy(i => i.inst_id)(_.values(insts))
    }
  },

  methods: {
    expand(inst_id, state) {
      console.log('expand', inst_id, state)
      Vue.set(this.expanded, inst_id, state)
    },

  },

  created() {
    const v = this
    this.runs_socket = new RunsSocket(undefined, undefined)
    this.runs_socket.open(
      (msg) => { v.runs = Object.assign({}, v.runs, msg.runs) })
  },

}

/*------------------------------------------------------------------------------
  run
------------------------------------------------------------------------------*/

const runs_template = `
<div>
 <br>
  <table class="runlist">
    <thead>
      <tr>
        <th>ID</th>
        <th>Job</th>
        <th>State</th>
        <th>Schedule</th>
        <th>Start</th>
        <th>Elapsed</th>
        <th>Actions</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="run in sorted" :key="run.run_id">
        <td class="run-link" v-on:click="$router.push({ name: 'run', params: { run_id: run.run_id } })">{{ run.run_id }}</td>
        <td class="job-link" v-on:click="$router.push({ name: 'job', params: { job_id: run.job_id } })">{{ run.job_id }}</td>
        <td>{{ run.state }}</td>
        <td>{{ run.times.schedule || "" }}</td>
        <td>{{ run.times.execute || "" }}</td>
        <td class="rt">{{ run.times.elapsed === undefined ? "" : format_elapsed(run.times.elapsed) }}</td>
        <td>
          <action-url
            v-for="(url, action) in run.actions" :url="url" :action="action">
          </action-url>
        </td>
      </tr>
    </tbody>
  </table>
</div>
`

class RunsSocket {
  constructor(run_id, job_id) {
    this.url = RunsSocket.get_url(run_id, job_id)
    this.websocket = null
  }

  open(callback) {
    this.websocket = new WebSocket(this.url)
    this.websocket.onmessage = (msg) => {
      const jso = JSON.parse(msg.data)
      callback(jso)
    }
    this.websocket.onclose = () => {
      console.log("web socket closed: " + this.url)
      this.websocket = null
    }
  }

  close() {
    if (this.websocket !== null)
      this.websocket.close
  }

  static get_url(run_id, job_id) {
    const url = new URL(location)
    url.protocol = 'ws'
    url.pathname = '/api/v1/runs-live'
    if (run_id !== undefined)
      url.searchParams.set('run_id', run_id)
    if (job_id !== undefined)
      url.searchParams.set('job_id', job_id)
    return url
  }
}


const Runs = Vue.component('runs', { 
  props: ['job_id'],
  template: runs_template,

  data() { 
    return { 
      runs_socket: null,
      runs: {},
    } 
  },

  computed: {
    sorted() {
      return _.flow(_.values, _.sortBy(r => r.times.schedule))(this.runs)
    },
  },

  methods: {
    format_elapsed,  // FIXME: Why do we need this?

  },

  created() {
    const v = this
    this.runs_socket = new RunsSocket(undefined, this.job_id)
    this.runs_socket.open(
      (msg) => { v.runs = Object.assign({}, v.runs, msg.runs) })
  },

  destroyed() {
    this.runs_socket.close()
  },
})

/*------------------------------------------------------------------------------
  run
------------------------------------------------------------------------------*/

const run_template = `
<div>
  <br>
  <div class="title">{{ run_id }}</div>
  <div v-if="run">
    <div>
      <a class="job-link" v-on:click="$router.push({ name: 'job', params: { job_id: run.job_id } })">{{ run.job_id }}</a>
      {{ arg_str }}
      #{{ run.number }}
    </div>
    <dl>
      <dt>state</dt>
      <dd>{{ run.state }}</dd>

      <dt>times</dt>
      <dd>
        <dl>
          <template v-for="[key, value] in run_times">
            <dt>{{ key }}</dt>
            <dd>{{ value }}</dd>
          </template>
        </dl>
      </dd>

      <template v-for="(value, key) in run.meta">
        <dt>{{ key }}</dt>
        <dd>{{ key == "elapsed" ? format_elapsed(value) : value }}</dd>  <!-- FIXME: Hack! -->
      </template>
    </dl>
    <h5>output</h5>
    <a v-if="run !== null && run.output_len !== null && output === null" v-on:click="load_output()">
      (load {{ run.output_len }} bytes)
    </a>
    <pre class="output" v-if="output !== null">{{ output }}</pre>
  </div>
</div>
`

const Run = {
  template: run_template,
  props: ['run_id'],
  data() {
    return {
      runs_socket: null,
      run: null,
      output: null,
    }
  },

  computed: {
    arg_str() {
      return _.flow([
        _.toPairs,
        _.map(([k, v]) => k + "=" + v),
        _.join(" ")
      ])(this.run.args)
    },

    run_times() {
      return _.flow(_.toPairs, _.sortBy(([k, v]) => v))(this.run.times)
    },
  },

  methods: {
    format_elapsed,  // FIXME: Why do we need this?

    load_output() {
      const v = this
      const url = "/api/v1/runs/" + this.run.run_id + "/output"  // FIXME
      fetch(url)
        // FIXME: Handle failure, set error.
        .then((response) => response.text())  // FIXME: Might not be text!
        .then((response) => { v.output = response })
    },
  },

  created() {
    const v = this
    this.runs_socket = new RunsSocket(this.run_id, undefined)
    this.runs_socket.open((msg) => { 
      v.run = msg.runs[v.run_id] 
      // Immediately load the output too, unless it's quite large.
      if (v.run.output_len !== null && v.run.output_len < 32768)
        v.load_output()
    })
  },

  destroyed() {
    this.runs_socket.close()
  },
}

/*------------------------------------------------------------------------------
------------------------------------------------------------------------------*/

// Each route should map to a component. The "component" can either be an
// actual component constructor created via `Vue.extend()`, or just a component
// options object.
const routes = [
  { path: '/jobs/:job_id', name: 'job', component: Job, props: true },
  { path: '/jobs', component: Jobs },
  { path: '/instances', component: Insts },
  { path: '/runs', component: Runs },
  { path: '/runs/:run_id', name: 'run', component: Run, props: true },
]

const router = new VueRouter({
  mode: 'history',
  routes: routes,
})

const app = new Vue({ router }).$mount('#app')

}

/*------------------------------------------------------------------------------
------------------------------------------------------------------------------*/

Vue.component('clock', {
  template: `
    <span>{{ time.toISOString().substr(0, 19) + 'Z' }}</span>
  `,

  data() {
    return {
      time: new Date(),
    }
  },

  mounted() {
    tick = () => {
      this.time = new Date()
      window.setTimeout(tick, 1000 - this.time % 1000)
    }
    tick()
  },
})

