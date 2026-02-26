<template>
  <div>
    <p style="font-size: 20px;">
      Esto está creado específicamente para poder mostrar sus estadísticas. 
      Con cada una podrá notar sus carencias o fortalezas.
    </p>

    <p style="font-size: 20px; display: flex; text-align: justify; flex-direction: column; align-items: center; justify-content: center; max-width: 47%; margin-left: 25%;">
      <strong>Estas son las pruebas</strong><br><br>
      Correr 15 metros y poner los segundos así: <strong>1.00</strong><br><br>
      Hacer la cantidad de flexiones que puedas (escribir solo el número, por ejemplo: 10)<br><br>
      Correr de 5 metros de lado a lado<br><br>
      Mantener la fuerza en concreto
    </p>

    <form @submit.prevent="agregarDatos" id="form">
      <input type="text" v-model="label" placeholder="Nombre" />
      <input type="number" v-model.number="time" placeholder="Velocidad" min="1" step="0.01" required />
      <input type="number" v-model.number="flexiones" placeholder="Flexiones" min="1" required />
      <input type="number" v-model.number="v3" placeholder="Resistencia" min="0" max="100" required />
      <input type="number" v-model.number="v4" placeholder="Agilidad" min="0" max="100" required />
      <input type="number" v-model.number="v5" placeholder="Potencia" min="0" max="100" required />
      <button type="submit">Agregar datos</button>
    </form>

    <canvas ref="radarChart" width="900" height="500"></canvas>

    <div id="statsList">
      <h3>Estadísticas Ingresadas:</h3>
      <div v-for="(entry, index) in entries" :key="index" class="stat-entry">
        <strong>{{ entry.label }}</strong><br><br>
        🏃 Velocidad: {{ entry.data[0].toFixed(1) }}<br><br>
        💪 Flexiones: {{ entry.data[1] }}<br><br>
        🏋️‍♂️ Resistencia: {{ entry.data[2] }}<br><br>
        🚀 Agilidad: {{ entry.data[3] }}<br><br>
        ⚽ Potencia: {{ entry.data[4] }}<br><br>
        <button @click="eliminar(index)">Eliminar {{ entry.label }}</button><br><br>
      </div>
    </div>
  </div>
</template>

<script>
import { Chart } from 'chart.js';


export default {
  name: 'RadarChart',
  data() {
    return {
      chart: null,
      label: '',
      time: null,
      flexiones: null,
      v3: null,
      v4: null,
      v5: null,
      counter: 1,
      entries: [],
    }
  },
  mounted() {
    const ctx = this.$refs.radarChart.getContext('2d');

    this.chart = new Chart(ctx, {
      type: 'radar',
      data: {
        labels: ['Velocidad', 'Flexiones', 'Resistencia', 'Agilidad', 'Potencia'],
        datasets: [],
      },
      options: {
        responsive: false,
        scales: {
          r: {
            min: 0,
            max: 100
          }
        },
        plugins: {
          legend: {
            position: 'top'
          }
        }
      }
    });
  },
  methods: {
    agregarDatos() {
      const labelFinal = this.label || `Test ${this.counter++}`;

      let speedEscala = 10;
      if (!isNaN(this.time) && this.time > 0) {
        const velocidad = 15 / this.time;
        speedEscala = Math.max(10, Math.min(100, velocidad * 10));
      }

      const flexionesEscala = Math.min(this.flexiones, 100);
      const values = [speedEscala, flexionesEscala, this.v3, this.v4, this.v5];

      const dataset = {
        label: labelFinal,
        data: values,
        fill: true,
        backgroundColor: 'rgba(255, 0, 0, 0.5)',
        borderColor: 'rgba(255, 0, 0, 1)',
        pointBackgroundColor: 'rgba(255, 0, 0, 1)'
      };

      this.chart.data.datasets.push(dataset);
      this.chart.update();

      this.entries.push({ label: labelFinal, data: values });

      // Limpiar formulario
      this.label = '';
      this.time = null;
      this.flexiones = null;
      this.v3 = null;
      this.v4 = null;
      this.v5 = null;
    },
    eliminar(index) {
      this.chart.data.datasets.splice(index, 1);
      this.chart.update();
      this.entries.splice(index, 1);
    }
  }
}
</script>

<style scoped>
form {
  margin: 20px 0;
}
.stat-entry {
  margin-bottom: 20px;
}
button {
  margin-top: 5px;
}
</style>
