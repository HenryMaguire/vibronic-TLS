from qutip import ket, mesolve, qeye, tensor, thermal_dm, destroy, steadystate
import matplotlib.pyplot as plt
import numpy as np
import UD_liouv as RC
import driving_liouv as diss
import ME_checking as check
reload(RC)
reload(diss)
reload(check)



def plot_dynamics():
    plt.figure()
    if T_EM>0.0: # No need to plot SS for T=0
        #ss_ns = steadystate(H, [L_RC+L_ns]).ptrace(0)
        ss_v = steadystate(H, [L_RC+L_s]).ptrace(0)
        ss_n = steadystate(H, [L_RC+L_naive]).ptrace(0)
        #ss_g_ns = ss_ns.matrix_element(G.dag(), G)
        ss_g_v = ss_v.matrix_element(G.dag(), G)
        ss_g_n = ss_n.matrix_element(G.dag(), G)
        plt.axhline(1-ss_g_v, color='b', ls='--')
        #plt.axhline(1-ss_g_ns, color='g', ls='--')
        plt.axhline(1-ss_g_n, color='r', ls='--')

    plt.title(r"$\omega_0=$""%i"r"$cm^{-1}$, $\alpha_{ph}=$""%f"r"$cm^{-1}$, $T_{EM}=$""%i K" %(w0, alpha_ph, T_EM))
    #plt.plot(timelist, 1-DATA_nrwa.expect[0], label='nrwa', color='y')
    plt.plot(timelist, 1-DATA_ns.expect[0].real, label='Non-secular', color='g')
    plt.plot(timelist, 1-DATA_s.expect[0].real, label='Vib. Lindblad', color='b')
    plt.plot(timelist, 1-DATA_naive.expect[0].real, label='Simple Lindblad', color='r')
    plt.ylabel("Excited state population")
    plt.xlabel("Time (cm)")
    plt.legend()
    p_file_name = "Notes/Images/Dynamics/Pop_a{:d}_Tph{:d}_Tem{:d}_w0{:d}.pdf".format(int(alpha_ph), int(T_ph), int(T_EM), int(w0))
    plt.savefig(p_file_name)
    plt.close()

    plt.figure()
    plt.title(r"$\alpha_{ph}=$""%i"r"$cm^{-1}$, $T_{EM}=$""%i K" %(alpha_ph, T_EM))
    plt.plot(timelist, DATA_s.expect[1].real, label='Vib. Lindblad', color='b')
    #plt.plot(timelist, DATA_ns.expect[1].real, label='Non-secular', color='g',alpha=0.7)
    plt.plot(timelist, DATA_naive.expect[1].real, label='Simple Lindblad', color='r',alpha=0.4)
    plt.legend()
    plt.ylabel("Coherence")
    plt.xlabel("Time (cm)")
    plt.xlim(0,2)
    file_name = "Notes/Images/Dynamics/Coh_a{:d}_Tph{:d}_Tem{:d}_w0{:d}.pdf".format(int(alpha_ph), int(T_ph), int(T_EM), int(w0))
    plt.savefig(file_name)
    plt.close()

def plot_dynamics_spec(DAT, t):
    dyn = 1-DAT.expect[1]
    plt.figure()
    ss = dyn[-1]
    gg = dyn-ss
    spec = np.fft.fft(gg)
    freq = np.fft.fftfreq(t.shape[-1])
    plt.plot(freq, abs(spec.real), label=r'$re(S)$')
    plt.plot(freq, abs(spec.imag), linestyle="dotted", label=r'$im(S)$')
    #plt.plot(freq, abs(spec), linestyle='dotted')
    plt.title("Frequency spectrum of vibronic TLS coherence")
    plt.legend()
    plt.ylabel("Magnitude" )
    plt.xlabel(r"Frequency- $\epsilon$ ($cm^{-1}$)")
    p_file_name = "Notes/Images/Spectra/Coh_spec_a{:d}_Tph{:d}_Tem{:d}_w0{:d}.pdf".format(int(alpha_ph), int(T_ph), int(T_EM), int(w0))
    plt.xlim(0, 0.5)
    plt.savefig(p_file_name)
    d_file_name = "DATA/Spectra/Coh_spec_a{:d}_Tph{:d}_TEM{:d}_w0{:d}.txt".format(int(alpha_ph), int(T_ph), int(T_EM), int(w0))
    np.savetxt(d_file_name, np.array([spec, freq]), delimiter = ',', newline= '\n')
    plt.close()

if __name__ == "__main__":

    N = 15
    G = ket([0])
    E = ket([1])
    sigma = G*E.dag() # Definition of a sigma_- operator.

    eps = 8000. # TLS splitting

    T_EM = 6000. # Optical bath temperature
    alpha_EM = 0.3 # System-bath strength (optical)

    T_ph = 100. # Phonon bath temperature
    wc = 53. # Ind.-Boson frame phonon cutoff freq
    w0 = 300. # underdamped SD parameter omega_0
    alpha_ph = 100. # Ind.-Boson frame coupling

    #Now we build all of the mapped operators and RC Liouvillian.
    L_RC, H, A_EM, A_nrwa, wRC, kappa= RC.RC_function_UD(sigma, eps, T_ph, wc, w0, alpha_ph, N)

    # electromagnetic bath liouvillians
    L_nrwa = diss.L_nonrwa(H, A_nrwa, alpha_EM, T_EM) # Ignore this for now as it just doesn't work
    L_ns = diss.L_nonsecular(H, A_EM, alpha_EM, T_EM)
    L_s = diss.L_vib_lindblad(H, A_EM, alpha_EM, T_EM)
    L_naive = diss.L_EM_lindblad(eps, A_EM, alpha_EM, T_EM)

    # Set up the initial density matrix
    n_RC = diss.Occupation(wRC, T_ph)
    #initial_sys = G*G.dag()
    #initial_sys = E*E.dag()
    initial_sys = 0.5*(G+E)*(E.dag()+G.dag())
    rho_0 = tensor(initial_sys, thermal_dm(N, n_RC))

    # Expectation values and time increments needed to calculate the dynamics
    expects = [tensor(G*G.dag(), qeye(N)), tensor(E*G.dag(), qeye(N)), tensor(qeye(2), destroy(N).dag()*destroy(N))]
    timelist = np.linspace(0,10,30000) # you need lots of points so that coherences are well defined -> spectra
    #nonsec_check(eps, H, A_em, N) # Plots a scatter graph representation of non-secularity. Could use nrwa instead.

    # Calculate dynamics
    #DATA_nrwa = mesolve(H, rho_0, timelist, [L_RC+L_nrwa], expects, progress_bar=True)
    DATA_ns = mesolve(H, rho_0, timelist, [L_RC+L_ns], expects, progress_bar=True)
    DATA_s = mesolve(H, rho_0, timelist, [L_RC+L_s], expects, progress_bar=True)
    DATA_naive = mesolve(H, rho_0, timelist, [L_RC+L_naive], expects, progress_bar=True)
    plot_dynamics()
    #SS, nvals = check.SS_convergence_check(eps, T_EM, T_ph, wc, w0, alpha_ph, alpha_EM, start_n=10)
    #plt.plot(nvals, SS)
    plot_dynamics_spec(DATA_s, timelist)

    np.savetxt('DATA/Dynamics/DATA_ns.txt', np.array([1- DATA_ns.expect[0], timelist]), delimiter = ',', newline= '\n')
