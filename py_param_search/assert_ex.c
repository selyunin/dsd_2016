#include <stdio.h>
#include <assert.h>
#include <stdint.h>
#include <stdbool.h>	// assumes at least C99

//DEFINE_TEST
//DEFINE_CBMC_CALL
#ifdef TEST
#include <stdlib.h>
#endif

#define PERIOD_LENGTH	50
#define MASK_UINT		0x00000FFF
#define MASK_INT		0x80000FF
#define MASK_BOOL		0x1
#define FALSE	false
#define TRUE	true

#define SIGN(x)		((x > 0) ? 1 : ((x < 0) ? -1 : 0))

#define NUM_SYNAPSES	(1) // default number of synapses
//DEFINE_NUM_SYNAPSES_DO_NOT_MODIFY THE LINE!

int fcn(//bool w[NUM_SYNAPSES], // synapse: w {0,1}
	//int32_t s[NUM_SYNAPSES], // synaptic weight: s {int}
	bool epsilon, // leak-reversal flag: epsilon {0,1}
	int16_t lambda, // leak weight: lambda
	uint32_t alpha, // positive threshold: alpha {uint}
	uint32_t beta, // negative threshold: beta {uint}
	uint32_t R, // reset voltage: R {int}
	uint8_t gamma, // reset mode {0,1,2}
	bool kappa) // saturation {0,1}
{
	// A: array of input spikes on axons,
	//   with dimension: (number_of_inputs x timesteps)
	//   values: boolean (1..spike, 0..no spike)
	//
	// e.g.:
	bool w[NUM_SYNAPSES] = {1};
	int32_t s[NUM_SYNAPSES] = {1};

	bool A[NUM_SYNAPSES][PERIOD_LENGTH] = {
		{true, false, false, true},
	};

	//LOAD_INPUTS_DO_NOT_MODIFY THE LINE!

	// bound values of parameters
	for(uint32_t i = 0; i < NUM_SYNAPSES; i++) {
		w[i] &= MASK_BOOL;
		s[i] &= MASK_INT;
	}
	epsilon &= MASK_BOOL;
	alpha &= MASK_UINT;
	beta &= MASK_UINT;
	R &= MASK_UINT;
	gamma &= 0x3;
	kappa &= MASK_BOOL;
	
	int32_t V = 0;
	int32_t V_store = 0;
	int32_t cnt = 0;

	bool spike = false;

#ifdef TEST
	const char* fname = "test";//INSERT_FILE_NAME
	FILE* fp = fopen(fname, "w+");
#endif

	for(uint32_t t = 0; t < PERIOD_LENGTH; t++) {
		// synaptic integration
		for(uint8_t i = 0; i < NUM_SYNAPSES; i++)
			V += A[i][t]*w[i]*s[i];

		// leak integration
		int8_t leak_direction = (1 - epsilon) + epsilon * SIGN(V);
		V += leak_direction * lambda;
		V_store = V;
		printf("V = %d\n", V);

		// threshold, fire, reset
		if (V > alpha) {
			// beyond positive threshold
			printf("Spike (V = %d)\n", V);
			spike = true;
			cnt++;
			switch (gamma) {
			case 0: V = R; break; // normal
			case 1: V -= alpha; break; // linear
			case 2: break; // no reset
			default: assert("reset mode '3' not available"); break;
			}
		} else if (V < -beta) {
			// beyond negative threshold
			spike = false;
			if (kappa) {
				V = -beta; // saturation
			} else {
				switch (gamma) {
				case 0: V = -R; break; // normal
				case 1: V += beta; break; // linear
				case 2: break; // no reset
				default: assert("reset mode '3' not available"); break;
				}
			}
		} else {
			spike = false;
		}
#ifdef TEST
		fprintf(fp,"%d,%d,%d\n",t,V_store,spike);
#endif
	}
	//ASSERT_STATEMENT_DO_NOT_MODIFY THE LINE!
#ifdef TEST
	fclose(fp);
#endif
	return cnt;
}

int main(int argc, char** argv)
{
	bool w[NUM_SYNAPSES] = {1};
	int32_t s[NUM_SYNAPSES] = {1};

	fcn(//w, s, // synapse and weight
	    0, //substitute_epsilon,
	    1, //substitute_lambda,
	    3, //substitute_alpha,
	    2, //substitute_beta,
	    0, //substitute_R,
	    0, //substitute_gamma,
	    0) //substitute_kappa)
	    ;

	return 0;
}
